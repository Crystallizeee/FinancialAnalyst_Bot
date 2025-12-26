"""
Market Data Module
Provides IHSG index, currency rates, and sector performance
"""
import yfinance as yf
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import IDX_SUFFIX


class MarketData:
    """Market data fetcher for IHSG, currencies, and sectors"""
    
    def __init__(self):
        # IDX Composite Index ticker
        self.ihsg_ticker = "^JKSE"
        
        # Currency pairs
        self.currency_pairs = {
            "USD/IDR": "USDIDR=X",
            "EUR/IDR": "EURIDR=X",
            "SGD/IDR": "SGDIDR=X",
            "JPY/IDR": "JPYIDR=X",
            "CNY/IDR": "CNYIDR=X",
            "AUD/IDR": "AUDIDR=X",
            "GBP/IDR": "GBPIDR=X",
        }
        
        # IDX Sectors with representative stocks
        self.sectors = {
            "Banking": ["BBCA", "BBRI", "BMRI", "BBNI", "BNGA"],
            "Mining": ["ADRO", "PTBA", "ITMG", "ANTM", "INCO"],
            "Consumer": ["UNVR", "ICBP", "INDF", "MYOR", "KLBF"],
            "Telecom": ["TLKM", "EXCL", "ISAT", "TOWR", "TBIG"],
            "Property": ["BSDE", "CTRA", "SMRA", "PWON", "LPKR"],
            "Infrastructure": ["JSMR", "WIKA", "WSKT", "PTPP", "ADHI"],
        }
    
    def get_ihsg_data(self) -> Optional[Dict[str, Any]]:
        """Get IHSG index data"""
        try:
            ticker = yf.Ticker(self.ihsg_ticker)
            info = ticker.info
            hist = ticker.history(period="5d")
            
            if hist.empty:
                return None
            
            current = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current
            change = current - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0
            
            # Get day's range
            today_high = hist["High"].iloc[-1]
            today_low = hist["Low"].iloc[-1]
            volume = hist["Volume"].iloc[-1]
            
            # Get 52-week data
            hist_1y = ticker.history(period="1y")
            week_52_high = hist_1y["High"].max() if not hist_1y.empty else 0
            week_52_low = hist_1y["Low"].min() if not hist_1y.empty else 0
            
            return {
                "name": "IHSG (IDX Composite)",
                "value": round(current, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "prev_close": round(prev_close, 2),
                "day_high": round(today_high, 2),
                "day_low": round(today_low, 2),
                "volume": int(volume),
                "week_52_high": round(week_52_high, 2),
                "week_52_low": round(week_52_low, 2),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching IHSG: {e}")
            return None
    
    def get_currency_rates(self) -> Dict[str, Dict[str, Any]]:
        """Get currency exchange rates to IDR"""
        rates = {}
        
        for name, ticker in self.currency_pairs.items():
            try:
                data = yf.Ticker(ticker)
                hist = data.history(period="2d")
                
                if not hist.empty:
                    current = hist["Close"].iloc[-1]
                    prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
                    change = current - prev
                    change_pct = (change / prev) * 100 if prev else 0
                    
                    rates[name] = {
                        "rate": round(current, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2)
                    }
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                continue
        
        return rates
    
    def get_single_currency(self, pair: str) -> Optional[Dict[str, Any]]:
        """Get single currency rate"""
        if pair not in self.currency_pairs:
            return None
        
        ticker = self.currency_pairs[pair]
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period="2d")
            
            if hist.empty:
                return None
            
            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
            change = current - prev
            change_pct = (change / prev) * 100 if prev else 0
            
            return {
                "pair": pair,
                "rate": round(current, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2)
            }
        except Exception as e:
            print(f"Error fetching {pair}: {e}")
            return None
    
    def format_ihsg_summary(self, data: Dict[str, Any]) -> str:
        """Format IHSG data into readable summary"""
        if not data:
            return "Data IHSG tidak tersedia"
        
        emoji = "🟢" if data["change"] >= 0 else "🔴"
        
        # Format volume
        vol = data["volume"]
        if vol == 0:
            vol_str = "Pasar Tutup"
        elif vol >= 1e9:
            vol_str = f"{vol/1e9:.2f}B"
        elif vol >= 1e6:
            vol_str = f"{vol/1e6:.2f}M"
        elif vol >= 1e3:
            vol_str = f"{vol/1e3:.2f}K"
        else:
            vol_str = str(int(vol))
        
        summary = f"""
📊 IHSG - Indeks Harga Saham Gabungan
━━━━━━━━━━━━━━━━━━━━━━

💰 Nilai: {data['value']:,.2f}
{emoji} Perubahan: {data['change']:+,.2f} ({data['change_pct']:+.2f}%)

📈 Hari Ini:
   • High: {data['day_high']:,.2f}
   • Low: {data['day_low']:,.2f}
   • Prev Close: {data['prev_close']:,.2f}

📊 52-Week Range:
   • High: {data['week_52_high']:,.2f}
   • Low: {data['week_52_low']:,.2f}

📦 Volume: {vol_str}

⏰ Updated: {data['last_updated'][:19]}
"""
        return summary.strip()
    
    def format_currency_summary(self, rates: Dict[str, Dict[str, Any]]) -> str:
        """Format currency rates into readable summary"""
        if not rates:
            return "Data kurs tidak tersedia"
        
        lines = ["💱 KURS MATA UANG (ke IDR)", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        for pair, data in rates.items():
            emoji = "🟢" if data["change"] >= 0 else "🔴"
            lines.append(f"{emoji} {pair}: Rp {data['rate']:,.2f}")
            lines.append(f"   Δ {data['change']:+,.2f} ({data['change_pct']:+.2f}%)")
            lines.append("")
        
        lines.append(f"⏰ Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(lines).strip()
    
    def get_sector_performance(self) -> Dict[str, float]:
        """
        Calculate average performance of each sector
        
        Returns:
            Dictionary of sector names and their average performance percentages
        """
        sector_perf = {}
        
        for sector_name, stocks in self.sectors.items():
            performances = []
            
            for stock in stocks:
                try:
                    ticker = yf.Ticker(f"{stock}{IDX_SUFFIX}")
                    hist = ticker.history(period="2d")
                    
                    if len(hist) >= 2:
                        current = hist["Close"].iloc[-1]
                        prev = hist["Close"].iloc[-2]
                        change_pct = ((current - prev) / prev) * 100 if prev else 0
                        performances.append(change_pct)
                except Exception:
                    continue
            
            if performances:
                sector_perf[sector_name] = sum(performances) / len(performances)
            else:
                sector_perf[sector_name] = 0.0
        
        return sector_perf
    
    def format_sector_performance(self, sector_perf: Dict[str, float]) -> str:
        """Format sector performance into readable summary"""
        if not sector_perf:
            return "Data sektor tidak tersedia"
        
        # Sort by performance
        sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
        
        lines = ["📊 PERFORMA SEKTOR", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        for sector, perf in sorted_sectors:
            emoji = "🟢" if perf >= 0 else "🔴"
            bar_len = min(int(abs(perf) * 2), 10)
            bar = "█" * bar_len if bar_len > 0 else "▏"
            lines.append(f"{emoji} {sector}: {perf:+.2f}%")
            lines.append(f"   {bar}")
            lines.append("")
        
        lines.append(f"⏰ Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(lines).strip()


# Singleton instance
market_data = MarketData()

