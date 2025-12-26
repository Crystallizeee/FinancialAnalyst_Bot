"""
Chart Generator Module
Creates stock price charts (candlestick, line) and sends as images
"""
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import IDX_SUFFIX, DATA_DIR


# Set matplotlib to use non-interactive backend
plt.switch_backend('Agg')

# Create charts directory
CHARTS_DIR = DATA_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


class ChartGenerator:
    """Generate stock price charts"""
    
    def __init__(self):
        # Custom style for dark theme
        self.style = {
            'base_mpl_style': 'dark_background',
            'marketcolors': mpf.make_marketcolors(
                up='#00ff00',
                down='#ff4444',
                edge='inherit',
                wick='inherit',
                volume='in'
            ),
            'mavcolors': ['#ff9800', '#2196f3', '#9c27b0'],
            'facecolor': '#1a1a2e',
            'gridcolor': '#333355',
            'gridstyle': '--',
            'y_on_right': True,
            'rc': {
                'font.size': 10,
                'axes.labelsize': 10,
                'axes.titlesize': 14,
            }
        }
        self.mpf_style = mpf.make_mpf_style(**self.style)
    
    def _get_ticker_symbol(self, stock_code: str) -> str:
        """Convert stock code to Yahoo Finance format"""
        stock_code = stock_code.upper().strip()
        if not stock_code.endswith(IDX_SUFFIX):
            return f"{stock_code}{IDX_SUFFIX}"
        return stock_code
    
    def generate_candlestick_chart(self, stock_code: str, period: str = "1mo") -> Optional[BytesIO]:
        """
        Generate candlestick chart for a stock
        
        Args:
            stock_code: Stock ticker
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y)
            
        Returns:
            BytesIO object containing the chart image
        """
        try:
            ticker = yf.Ticker(self._get_ticker_symbol(stock_code))
            df = ticker.history(period=period)
            
            if df.empty:
                return None
            
            # Create the chart
            fig, axes = mpf.plot(
                df,
                type='candle',
                style=self.mpf_style,
                title=f'{stock_code.upper()} - {period.upper()}',
                ylabel='Price (Rp)',
                ylabel_lower='Volume',
                volume=True,
                mav=(5, 20),
                figsize=(12, 8),
                returnfig=True,
                tight_layout=True
            )
            
            # Save to BytesIO
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            
            return buf
            
        except Exception as e:
            print(f"Error generating candlestick chart: {e}")
            return None
    
    def generate_line_chart(self, stock_code: str, period: str = "1mo") -> Optional[BytesIO]:
        """
        Generate simple line chart for a stock
        
        Args:
            stock_code: Stock ticker
            period: Time period
            
        Returns:
            BytesIO object containing the chart image
        """
        try:
            ticker = yf.Ticker(self._get_ticker_symbol(stock_code))
            df = ticker.history(period=period)
            
            if df.empty:
                return None
            
            # Create the chart
            fig, ax = plt.subplots(figsize=(12, 6), facecolor='#1a1a2e')
            ax.set_facecolor('#1a1a2e')
            
            # Plot price line
            ax.plot(df.index, df['Close'], color='#00ff00', linewidth=2, label='Close')
            
            # Add moving averages
            if len(df) >= 5:
                df['MA5'] = df['Close'].rolling(window=5).mean()
                ax.plot(df.index, df['MA5'], color='#ff9800', linewidth=1, label='MA5', linestyle='--')
            
            if len(df) >= 20:
                df['MA20'] = df['Close'].rolling(window=20).mean()
                ax.plot(df.index, df['MA20'], color='#2196f3', linewidth=1, label='MA20', linestyle='--')
            
            # Fill area under the line
            ax.fill_between(df.index, df['Close'], alpha=0.3, color='#00ff00')
            
            # Styling
            ax.set_title(f'{stock_code.upper()} - {period.upper()}', color='white', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date', color='white')
            ax.set_ylabel('Price (Rp)', color='white')
            ax.tick_params(colors='white')
            ax.legend(facecolor='#1a1a2e', edgecolor='white', labelcolor='white')
            ax.grid(True, alpha=0.3, color='#333355')
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            plt.xticks(rotation=45)
            
            # Add current price annotation
            current_price = df['Close'].iloc[-1]
            ax.annotate(f'Rp {current_price:,.0f}', 
                       xy=(df.index[-1], current_price),
                       xytext=(10, 10), textcoords='offset points',
                       color='#00ff00', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            
            # Save to BytesIO
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            
            return buf
            
        except Exception as e:
            print(f"Error generating line chart: {e}")
            return None
    
    def generate_comparison_chart(self, stock_codes: list, period: str = "1mo") -> Optional[BytesIO]:
        """
        Generate comparison chart for multiple stocks (normalized)
        
        Args:
            stock_codes: List of stock tickers
            period: Time period
            
        Returns:
            BytesIO object containing the chart image
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6), facecolor='#1a1a2e')
            ax.set_facecolor('#1a1a2e')
            
            colors = ['#00ff00', '#ff4444', '#2196f3', '#ff9800', '#9c27b0']
            
            for i, stock_code in enumerate(stock_codes[:5]):  # Max 5 stocks
                ticker = yf.Ticker(self._get_ticker_symbol(stock_code))
                df = ticker.history(period=period)
                
                if not df.empty:
                    # Normalize to percentage change from first value
                    normalized = (df['Close'] / df['Close'].iloc[0] - 1) * 100
                    ax.plot(df.index, normalized, color=colors[i], linewidth=2, 
                           label=stock_code.upper())
            
            # Styling
            ax.set_title(f'Stock Comparison - {period.upper()}', color='white', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date', color='white')
            ax.set_ylabel('Change (%)', color='white')
            ax.tick_params(colors='white')
            ax.legend(facecolor='#1a1a2e', edgecolor='white', labelcolor='white')
            ax.grid(True, alpha=0.3, color='#333355')
            ax.axhline(y=0, color='white', linestyle='-', linewidth=0.5)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save to BytesIO
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            
            return buf
            
        except Exception as e:
            print(f"Error generating comparison chart: {e}")
            return None
    
    def generate_sector_performance_chart(self, sectors_data: Dict[str, float]) -> Optional[BytesIO]:
        """
        Generate sector performance bar chart
        
        Args:
            sectors_data: Dictionary of sector names and their performance percentages
            
        Returns:
            BytesIO object containing the chart image
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6), facecolor='#1a1a2e')
            ax.set_facecolor('#1a1a2e')
            
            sectors = list(sectors_data.keys())
            values = list(sectors_data.values())
            colors = ['#00ff00' if v >= 0 else '#ff4444' for v in values]
            
            bars = ax.barh(sectors, values, color=colors, edgecolor='white', linewidth=0.5)
            
            # Add value labels
            for bar, value in zip(bars, values):
                width = bar.get_width()
                ax.annotate(f'{value:+.2f}%',
                           xy=(width, bar.get_y() + bar.get_height()/2),
                           xytext=(5, 0), textcoords='offset points',
                           ha='left' if width >= 0 else 'right',
                           va='center', color='white', fontsize=10)
            
            # Styling
            ax.set_title('Sector Performance', color='white', fontsize=14, fontweight='bold')
            ax.set_xlabel('Change (%)', color='white')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.3, color='#333355', axis='x')
            ax.axvline(x=0, color='white', linestyle='-', linewidth=0.5)
            
            plt.tight_layout()
            
            # Save to BytesIO
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            
            return buf
            
        except Exception as e:
            print(f"Error generating sector chart: {e}")
            return None


# Singleton instance
chart_generator = ChartGenerator()
