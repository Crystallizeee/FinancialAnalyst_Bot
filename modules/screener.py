"""
Screener Module
Filter and screen stocks based on criteria
"""
import yfinance as yf
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import IDX_SUFFIX, POPULAR_IDX_STOCKS


class StockScreener:
    """Screen stocks based on various criteria"""
    
    def __init__(self):
        # Default stock universe to screen
        self.stock_universe = POPULAR_IDX_STOCKS
    
    def _get_ticker_symbol(self, stock_code: str) -> str:
        """Convert stock code to Yahoo Finance format"""
        stock_code = stock_code.upper().strip()
        if not stock_code.endswith(IDX_SUFFIX):
            return f"{stock_code}{IDX_SUFFIX}"
        return stock_code
    
    def _normalize_dividend_yield(self, value) -> float:
        """
        Normalize dividend yield to decimal format.
        Yahoo Finance sometimes returns as percentage (8.95) or decimal (0.0895)
        """
        if value is None:
            return 0.0
        try:
            value = float(value)
            if value > 1:  # It's a percentage, convert to decimal
                return value / 100
            return value
        except (TypeError, ValueError):
            return 0.0
    
    def get_stock_metrics(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """Get key metrics for a stock"""
        try:
            ticker = yf.Ticker(self._get_ticker_symbol(stock_code))
            info = ticker.info
            
            if not info:
                return None
            
            raw_dividend = info.get("dividendYield", 0)
            
            return {
                "symbol": stock_code.upper(),
                "name": info.get("longName", info.get("shortName", stock_code)),
                "price": info.get("regularMarketPrice", 0),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": self._normalize_dividend_yield(raw_dividend),
                "market_cap": info.get("marketCap", 0),
                "volume": info.get("regularMarketVolume", 0),
                "change_pct": ((info.get("regularMarketPrice", 0) - info.get("regularMarketPreviousClose", 1)) / 
                              info.get("regularMarketPreviousClose", 1) * 100) if info.get("regularMarketPreviousClose") else 0,
            }
        except Exception as e:
            print(f"Error getting metrics for {stock_code}: {e}")
            return None
    
    def screen_by_pe(self, max_pe: float = 15.0) -> List[Dict[str, Any]]:
        """Screen for low P/E stocks"""
        results = []
        
        for stock in self.stock_universe:
            metrics = self.get_stock_metrics(stock)
            if metrics and metrics["pe_ratio"] and metrics["pe_ratio"] <= max_pe and metrics["pe_ratio"] > 0:
                results.append(metrics)
        
        return sorted(results, key=lambda x: x["pe_ratio"])
    
    def screen_by_dividend(self, min_yield: float = 0.03) -> List[Dict[str, Any]]:
        """Screen for high dividend yield stocks"""
        results = []
        
        for stock in self.stock_universe:
            metrics = self.get_stock_metrics(stock)
            if metrics and metrics["dividend_yield"] and metrics["dividend_yield"] >= min_yield:
                results.append(metrics)
        
        return sorted(results, key=lambda x: x["dividend_yield"], reverse=True)
    
    def screen_by_pb(self, max_pb: float = 1.5) -> List[Dict[str, Any]]:
        """Screen for low P/B (undervalued) stocks"""
        results = []
        
        for stock in self.stock_universe:
            metrics = self.get_stock_metrics(stock)
            if metrics and metrics["pb_ratio"] and metrics["pb_ratio"] <= max_pb and metrics["pb_ratio"] > 0:
                results.append(metrics)
        
        return sorted(results, key=lambda x: x["pb_ratio"])
    
    def screen_top_gainers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top gaining stocks"""
        results = []
        
        for stock in self.stock_universe:
            metrics = self.get_stock_metrics(stock)
            if metrics:
                results.append(metrics)
        
        return sorted(results, key=lambda x: x["change_pct"], reverse=True)[:limit]
    
    def screen_top_losers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top losing stocks"""
        results = []
        
        for stock in self.stock_universe:
            metrics = self.get_stock_metrics(stock)
            if metrics:
                results.append(metrics)
        
        return sorted(results, key=lambda x: x["change_pct"])[:limit]
    
    def screen_custom(self, 
                      max_pe: float = None, 
                      max_pb: float = None, 
                      min_dividend: float = None,
                      min_market_cap: float = None) -> List[Dict[str, Any]]:
        """Custom screening with multiple criteria"""
        results = []
        
        for stock in self.stock_universe:
            metrics = self.get_stock_metrics(stock)
            if not metrics:
                continue
            
            # Apply filters
            if max_pe and (not metrics["pe_ratio"] or metrics["pe_ratio"] > max_pe):
                continue
            if max_pb and (not metrics["pb_ratio"] or metrics["pb_ratio"] > max_pb):
                continue
            if min_dividend and (not metrics["dividend_yield"] or metrics["dividend_yield"] < min_dividend):
                continue
            if min_market_cap and (not metrics["market_cap"] or metrics["market_cap"] < min_market_cap):
                continue
            
            results.append(metrics)
        
        return results
    
    def format_screener_results(self, results: List[Dict[str, Any]], title: str) -> str:
        """Format screener results into readable summary"""
        if not results:
            return f"📊 {title}\n\nTidak ada saham yang memenuhi kriteria."
        
        lines = [f"📊 {title}", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        for i, stock in enumerate(results[:10], 1):  # Limit to 10
            pe = f"{stock['pe_ratio']:.1f}" if stock['pe_ratio'] else "N/A"
            pb = f"{stock['pb_ratio']:.1f}" if stock['pb_ratio'] else "N/A"
            div = f"{stock['dividend_yield']*100:.1f}%" if stock['dividend_yield'] else "0%"
            change = f"{stock['change_pct']:+.1f}%"
            
            change_emoji = "🟢" if stock['change_pct'] >= 0 else "🔴"
            
            lines.append(f"{i}. {stock['symbol']} - Rp {stock['price']:,.0f}")
            lines.append(f"   {change_emoji} {change} | P/E: {pe} | P/B: {pb} | Div: {div}")
            lines.append("")
        
        return "\n".join(lines).strip()


# Singleton instance
stock_screener = StockScreener()
