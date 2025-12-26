"""
Stock Data Fetcher Module
Fetches real-time stock data from Yahoo Finance for IDX stocks
"""
import yfinance as yf
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import sys
sys.path.append('..')
from config.settings import IDX_SUFFIX, POPULAR_IDX_STOCKS


class StockDataFetcher:
    """Fetches and processes stock data from Yahoo Finance"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_duration = timedelta(minutes=5)
    
    def _get_ticker_symbol(self, stock_code: str) -> str:
        """Convert stock code to Yahoo Finance format"""
        stock_code = stock_code.upper().strip()
        if not stock_code.endswith(IDX_SUFFIX):
            return f"{stock_code}{IDX_SUFFIX}"
        return stock_code
    
    def _is_cache_valid(self, stock_code: str) -> bool:
        """Check if cached data is still valid"""
        if stock_code not in self.cache:
            return False
        cached_time = self.cache[stock_code].get("timestamp")
        if not cached_time:
            return False
        return datetime.now() - cached_time < self.cache_duration
    
    def _normalize_dividend_yield(self, value) -> float:
        """
        Normalize dividend yield to decimal format.
        Yahoo Finance sometimes returns as percentage (8.95) or decimal (0.0895)
        We normalize to decimal so 8.95% becomes 0.0895
        """
        if value is None:
            return 0.0
        
        try:
            value = float(value)
            # If value > 1, it's likely a percentage (e.g., 8.95 means 8.95%)
            # Convert to decimal format
            if value > 1:
                return value / 100
            return value
        except (TypeError, ValueError):
            return 0.0
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive stock information
        
        Args:
            stock_code: Stock ticker (e.g., 'BBCA')
            
        Returns:
            Dictionary with stock info or None if not found
        """
        # Check cache first
        if self._is_cache_valid(stock_code):
            return self.cache[stock_code]["data"]
        
        try:
            ticker_symbol = self._get_ticker_symbol(stock_code)
            ticker = yf.Ticker(ticker_symbol)
            
            # Get stock info
            info = ticker.info
            
            if not info or info.get("regularMarketPrice") is None:
                return None
            
            # Get historical data for change calculation
            hist = ticker.history(period="5d")
            
            # Calculate price change
            current_price = info.get("regularMarketPrice", 0)
            prev_close = info.get("regularMarketPreviousClose", current_price)
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close * 100) if prev_close else 0
            
            # Get 52-week data
            week_52_high = info.get("fiftyTwoWeekHigh", 0)
            week_52_low = info.get("fiftyTwoWeekLow", 0)
            
            stock_data = {
                "symbol": stock_code.upper(),
                "name": info.get("longName", info.get("shortName", stock_code)),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                
                # Price data
                "current_price": current_price,
                "previous_close": prev_close,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "currency": info.get("currency", "IDR"),
                
                # Trading data
                "volume": info.get("regularMarketVolume", 0),
                "avg_volume": info.get("averageVolume", 0),
                "market_cap": info.get("marketCap", 0),
                
                # Valuation
                "pe_ratio": info.get("trailingPE", None),
                "forward_pe": info.get("forwardPE", None),
                "pb_ratio": info.get("priceToBook", None),
                # Normalize dividend yield to decimal (0.05 = 5%)
                # Yahoo Finance sometimes returns as percentage (5.0) or decimal (0.05)
                "dividend_yield": self._normalize_dividend_yield(info.get("dividendYield", 0)),
                
                # 52-week range
                "week_52_high": week_52_high,
                "week_52_low": week_52_low,
                "from_52_high_pct": ((current_price - week_52_high) / week_52_high * 100) if week_52_high else 0,
                "from_52_low_pct": ((current_price - week_52_low) / week_52_low * 100) if week_52_low else 0,
                
                # Additional info
                "beta": info.get("beta", None),
                "eps": info.get("trailingEps", None),
                
                # Timestamp
                "last_updated": datetime.now().isoformat(),
            }
            
            # Cache the data
            self.cache[stock_code] = {
                "data": stock_data,
                "timestamp": datetime.now()
            }
            
            return stock_data
            
        except Exception as e:
            print(f"Error fetching stock data for {stock_code}: {e}")
            return None
    
    def get_stock_history(self, stock_code: str, period: str = "1mo") -> Optional[Dict[str, Any]]:
        """
        Get historical stock data
        
        Args:
            stock_code: Stock ticker
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            
        Returns:
            Dictionary with historical data
        """
        try:
            ticker_symbol = self._get_ticker_symbol(stock_code)
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            return {
                "symbol": stock_code.upper(),
                "period": period,
                "data": hist.to_dict(),
                "summary": {
                    "start_price": hist["Close"].iloc[0] if len(hist) > 0 else 0,
                    "end_price": hist["Close"].iloc[-1] if len(hist) > 0 else 0,
                    "high": hist["High"].max(),
                    "low": hist["Low"].min(),
                    "avg_volume": hist["Volume"].mean(),
                    "total_return_pct": ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0] * 100) if len(hist) > 0 else 0,
                }
            }
            
        except Exception as e:
            print(f"Error fetching history for {stock_code}: {e}")
            return None
    
    def get_multiple_stocks(self, stock_codes: list) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get data for multiple stocks
        
        Args:
            stock_codes: List of stock tickers
            
        Returns:
            Dictionary mapping stock codes to their data
        """
        results = {}
        for code in stock_codes:
            results[code] = self.get_stock_info(code)
        return results
    
    def format_stock_summary(self, stock_data: Dict[str, Any]) -> str:
        """
        Format stock data into readable summary
        
        Args:
            stock_data: Stock data dictionary
            
        Returns:
            Formatted string
        """
        if not stock_data:
            return "Data tidak tersedia"
        
        # Helper function for safe number handling
        def safe_num(value, default=0):
            return value if value is not None else default
        
        change_emoji = "🟢" if safe_num(stock_data.get("price_change", 0)) >= 0 else "🔴"
        
        # Format market cap
        market_cap = safe_num(stock_data.get("market_cap", 0))
        if market_cap >= 1e12:
            market_cap_str = f"Rp {market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            market_cap_str = f"Rp {market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            market_cap_str = f"Rp {market_cap/1e6:.2f}M"
        else:
            market_cap_str = "N/A"
        
        # Format volume
        volume = safe_num(stock_data.get("volume", 0))
        if volume >= 1e9:
            volume_str = f"{volume/1e9:.2f}B"
        elif volume >= 1e6:
            volume_str = f"{volume/1e6:.2f}M"
        elif volume >= 1e3:
            volume_str = f"{volume/1e3:.2f}K"
        else:
            volume_str = str(int(volume)) if volume else "N/A"
        
        # Safe value extraction
        current_price = safe_num(stock_data.get('current_price', 0))
        price_change = safe_num(stock_data.get('price_change', 0))
        price_change_pct = safe_num(stock_data.get('price_change_pct', 0))
        week_52_high = safe_num(stock_data.get('week_52_high', 0))
        week_52_low = safe_num(stock_data.get('week_52_low', 0))
        from_52_high_pct = safe_num(stock_data.get('from_52_high_pct', 0))
        from_52_low_pct = safe_num(stock_data.get('from_52_low_pct', 0))
        
        # Format PE and PB ratio
        pe_ratio = stock_data.get('pe_ratio')
        pb_ratio = stock_data.get('pb_ratio')
        pe_str = f"{pe_ratio:.2f}" if pe_ratio is not None else "N/A"
        pb_str = f"{pb_ratio:.2f}" if pb_ratio is not None else "N/A"
        
        # Dividend yield
        div_yield = safe_num(stock_data.get('dividend_yield', 0))
        div_str = f"{div_yield*100:.2f}%"
        
        summary = f"""
📊 {stock_data.get('symbol', 'N/A')} - {stock_data.get('name', 'Unknown')}
━━━━━━━━━━━━━━━━━━━━━━

💰 Harga: Rp {current_price:,.0f}
{change_emoji} Perubahan: Rp {price_change:+,.0f} ({price_change_pct:+.2f}%)

📈 52-Week Range:
   • High: Rp {week_52_high:,.0f} ({from_52_high_pct:.1f}%)
   • Low: Rp {week_52_low:,.0f} ({from_52_low_pct:+.1f}%)

📊 Trading:
   • Volume: {volume_str}
   • Market Cap: {market_cap_str}

📉 Valuasi:
   • P/E Ratio: {pe_str}
   • P/B Ratio: {pb_str}
   • Dividend Yield: {div_str}

🏢 Sektor: {stock_data.get('sector', 'N/A')}
🏭 Industri: {stock_data.get('industry', 'N/A')}

⏰ Updated: {stock_data.get('last_updated', 'N/A')[:19]}
"""
        return summary.strip()


# Singleton instance
stock_fetcher = StockDataFetcher()
