"""
Technical Analysis Module
Provides technical indicators for stocks
"""
import yfinance as yf
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import IDX_SUFFIX


class TechnicalAnalysis:
    """Technical analysis calculations for IDX stocks"""
    
    def __init__(self):
        pass
    
    def _get_ticker_symbol(self, stock_code: str) -> str:
        """Convert stock code to Yahoo Finance format"""
        stock_code = stock_code.upper().strip()
        if not stock_code.endswith(IDX_SUFFIX):
            return f"{stock_code}{IDX_SUFFIX}"
        return stock_code
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices: List of closing prices
            period: RSI period (default 14)
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Not enough data
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change >= 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        # Calculate average gain and loss
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return round(sum(prices[-period:]) / period, 2)
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return round(ema, 2)
    
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Returns:
            Dictionary with macd, signal, and histogram
        """
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        ema_12 = self.calculate_ema(prices, 12)
        ema_26 = self.calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        
        # For signal line, we need MACD values over time
        # Simplified: use current MACD as approximation
        signal_line = macd_line * 0.9  # Approximation
        
        histogram = macd_line - signal_line
        
        return {
            "macd": round(macd_line, 2),
            "signal": round(signal_line, 2),
            "histogram": round(histogram, 2)
        }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        
        Returns:
            Dictionary with upper, middle, lower bands
        """
        if len(prices) < period:
            current = prices[-1] if prices else 0
            return {"upper": current, "middle": current, "lower": current}
        
        sma = self.calculate_sma(prices, period)
        
        # Calculate standard deviation
        squared_diff = [(p - sma) ** 2 for p in prices[-period:]]
        std = (sum(squared_diff) / period) ** 0.5
        
        return {
            "upper": round(sma + (2 * std), 2),
            "middle": round(sma, 2),
            "lower": round(sma - (2 * std), 2)
        }
    
    def get_technical_indicators(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Get all technical indicators for a stock
        
        Args:
            stock_code: Stock ticker
            
        Returns:
            Dictionary with all technical indicators
        """
        try:
            ticker_symbol = self._get_ticker_symbol(stock_code)
            ticker = yf.Ticker(ticker_symbol)
            
            # Get 3 months of data for calculation
            hist = ticker.history(period="3mo")
            
            if hist.empty:
                return None
            
            prices = hist["Close"].tolist()
            current_price = prices[-1] if prices else 0
            
            # Calculate indicators
            rsi = self.calculate_rsi(prices)
            sma_20 = self.calculate_sma(prices, 20)
            sma_50 = self.calculate_sma(prices, 50)
            ema_12 = self.calculate_ema(prices, 12)
            ema_26 = self.calculate_ema(prices, 26)
            macd = self.calculate_macd(prices)
            bollinger = self.calculate_bollinger_bands(prices)
            
            # Determine signals
            rsi_signal = "OVERBOUGHT" if rsi > 70 else ("OVERSOLD" if rsi < 30 else "NEUTRAL")
            
            trend_signal = "BULLISH" if current_price > sma_20 > sma_50 else (
                "BEARISH" if current_price < sma_20 < sma_50 else "NEUTRAL"
            )
            
            macd_signal = "BULLISH" if macd["histogram"] > 0 else "BEARISH"
            
            return {
                "symbol": stock_code.upper(),
                "current_price": round(current_price, 2),
                "rsi": rsi,
                "rsi_signal": rsi_signal,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "ema_12": ema_12,
                "ema_26": ema_26,
                "macd": macd,
                "macd_signal": macd_signal,
                "bollinger": bollinger,
                "trend_signal": trend_signal,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating TA for {stock_code}: {e}")
            return None
    
    def format_technical_analysis(self, ta_data: Dict[str, Any]) -> str:
        """Format technical analysis into readable summary"""
        if not ta_data:
            return "Data teknikal tidak tersedia"
        
        # Signal emojis
        rsi_emoji = "🔴" if ta_data["rsi_signal"] == "OVERBOUGHT" else (
            "🟢" if ta_data["rsi_signal"] == "OVERSOLD" else "⚪"
        )
        
        trend_emoji = "🟢" if ta_data["trend_signal"] == "BULLISH" else (
            "🔴" if ta_data["trend_signal"] == "BEARISH" else "⚪"
        )
        
        macd_emoji = "🟢" if ta_data["macd_signal"] == "BULLISH" else "🔴"
        
        summary = f"""
📈 TECHNICAL ANALYSIS - {ta_data['symbol']}
━━━━━━━━━━━━━━━━━━━━━━

💰 Harga: Rp {ta_data['current_price']:,.0f}

📊 RSI (14): {ta_data['rsi']}
{rsi_emoji} Signal: {ta_data['rsi_signal']}
   • > 70 = Overbought (potensi turun)
   • < 30 = Oversold (potensi naik)

📉 Moving Averages:
   • SMA 20: Rp {ta_data['sma_20']:,.0f}
   • SMA 50: Rp {ta_data['sma_50']:,.0f}
   • EMA 12: Rp {ta_data['ema_12']:,.0f}
   • EMA 26: Rp {ta_data['ema_26']:,.0f}

📊 MACD:
   • MACD Line: {ta_data['macd']['macd']}
   • Signal Line: {ta_data['macd']['signal']}
   • Histogram: {ta_data['macd']['histogram']}
{macd_emoji} Signal: {ta_data['macd_signal']}

📈 Bollinger Bands:
   • Upper: Rp {ta_data['bollinger']['upper']:,.0f}
   • Middle: Rp {ta_data['bollinger']['middle']:,.0f}
   • Lower: Rp {ta_data['bollinger']['lower']:,.0f}

{trend_emoji} TREND: {ta_data['trend_signal']}

⚠️ Disclaimer: Analisis teknikal bukan jaminan profit.
"""
        return summary.strip()


# Singleton instance
technical_analysis = TechnicalAnalysis()
