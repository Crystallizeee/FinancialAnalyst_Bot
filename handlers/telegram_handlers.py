"""
Telegram Bot Handlers
Implements all bot commands and message handlers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import asyncio
import sys
import logging
import traceback

sys.path.append('..')

from modules.stock_data import StockDataFetcher
from modules.gemini_ai import GeminiAI
from modules.serper_search import SerperSearch
from modules.portfolio import PortfolioManager
from modules.alerts import AlertManager
from modules.technical_analysis import TechnicalAnalysis
from modules.watchlist import WatchlistManager
from modules.screener import StockScreener
from modules.market_data import MarketData
from modules.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)

# Telegram message limit
MAX_MESSAGE_LENGTH = 4000  # Leave buffer for formatting

# Initialize modules
stock_fetcher = StockDataFetcher()
gemini_ai = GeminiAI()
serper_search = SerperSearch()
portfolio_manager = PortfolioManager()
alert_manager = AlertManager()
technical_analysis = TechnicalAnalysis()
watchlist_manager = WatchlistManager()
stock_screener = StockScreener()
market_data_fetcher = MarketData()
chart_generator = ChartGenerator()

# Notifications
from modules.notifications import NotificationManager
notification_manager = NotificationManager()

# Portfolio Analysis
from modules.portfolio_analysis import PortfolioAnalyzer
portfolio_analyzer = PortfolioAnalyzer()

# User Profiles
from modules.user_profile import UserProfileManager
user_profile_manager = UserProfileManager()


def clean_markdown(text: str) -> str:
    """Remove markdown formatting from text for clean Telegram display"""
    import re
    
    # Remove headers (### Header, ## Header, # Header)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Remove italic (*text* or _text_) - be careful not to break underscores in words
    text = re.sub(r'(?<!\w)\*([^*]+?)\*(?!\w)', r'\1', text)
    text = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'\1', text)
    
    # Remove code blocks (```code```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove inline code (`code`)
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    
    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+?)\]\([^)]+?\)', r'\1', text)
    
    # Remove horizontal rules (---, ***, ___)
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # Remove bullet points (- item, * item) but keep the content
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    
    # Remove numbered lists formatting but keep numbers
    text = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list:
    """Split a long message into chunks that fit Telegram's limit"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by lines first to keep formatting
    lines = text.split('\n')
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # If single line is too long, split by words
            if len(line) > max_length:
                words = line.split(' ')
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= max_length:
                        current_chunk += word + ' '
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = word + ' '
            else:
                current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


async def send_long_message(update: Update, text: str):
    """Send a message, cleaning markdown and splitting if too long"""
    # Clean markdown formatting
    clean_text = clean_markdown(text)
    
    # Split if needed
    chunks = split_message(clean_text)
    
    for chunk in chunks:
        await update.message.reply_text(chunk)



# ============== Command Handlers ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = """
🤖 **AI Financial Advisor**
━━━━━━━━━━━━━━━━━━━━━━

📊 **ANALISIS & RESEARCH**
/analyze <kode> - Analisis lengkap
/recommend <kode> - Rekomendasi AI
/news <kode> - Berita terkini
/ta <kode> - Technical analysis
/compare <A> <B> - Bandingkan saham
/screener <filter> - Stock screener

📈 **MARKET DATA**
/ihsg - Data IHSG real-time
/kurs - Nilai tukar mata uang
/sector - Kinerja sektor
/market - Update pasar

📊 **CHARTS**
/chart <kode> [period] - Candlestick chart
/comparechart <A> <B> - Comparison chart

💼 **PORTFOLIO**
/portfolio - Lihat portfolio
/buy <kode> <qty> <harga> - Catat beli
/sell <kode> <qty> <harga> - Catat jual
/history - Riwayat transaksi
/diversify - Analisis diversifikasi
/export <pdf/excel> - Export laporan

🔔 **ALERTS & NOTIFICATIONS**
/alert <kode> <above/below> <harga>
/alerts - Lihat semua alert
/deletealert <id> - Hapus alert
/subscribe - Langganan notifikasi
/watchlist - Kelola watchlist

🤖 **AI PRO**
/profile - Set profil risiko
/advice - Saran personal AI
/predict <kode> - Prediksi tren AI
/ask <pertanyaan> - Tanya AI

📱 /menu - Menu interaktif

⚠️ DISCLAIMER: Bukan nasihat finansial profesional.
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await start_command(update, context)


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analyze <stock_code> command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Format: /analyze <kode_saham>\nContoh: /analyze BBCA"
        )
        return
    
    stock_code = context.args[0].upper()
    await update.message.reply_text(f"🔄 Menganalisis {stock_code}...")
    
    try:
        # Get stock data
        stock_data = stock_fetcher.get_stock_info(stock_code)
        
        if not stock_data:
            await update.message.reply_text(
                f"❌ Saham {stock_code} tidak ditemukan. Pastikan kode saham benar."
            )
            return
        
        # Get news
        news_items = await serper_search.search_stock_news(stock_code, stock_data.get("name", ""))
        news_summary = " | ".join(serper_search.extract_headlines(news_items)[:5])
        
        # Get AI analysis
        analysis = await gemini_ai.analyze_stock(stock_data, news_summary)
        
        # Send stock summary first
        summary = stock_fetcher.format_stock_summary(stock_data)
        await send_long_message(update, summary)
        
        # Send AI analysis (may be long)
        await send_long_message(update, f"🤖 AI Analysis:\n\n{analysis}")
            
    except Exception as e:
        logger.error(f"Error in analyze_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")



async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /recommend <stock_code> command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Format: /recommend <kode_saham>\nContoh: /recommend BBCA"
        )
        return
    
    stock_code = context.args[0].upper()
    await update.message.reply_text(f"🔄 Generating recommendation for {stock_code}...")
    
    try:
        # Get stock data
        stock_data = stock_fetcher.get_stock_info(stock_code)
        
        if not stock_data:
            await update.message.reply_text(
                f"❌ Saham {stock_code} tidak ditemukan."
            )
            return
        
        # Get recommendation
        recommendation = await gemini_ai.get_recommendation(stock_data)
        
        await send_long_message(update, f"🎯 Rekomendasi untuk {stock_code}:\n\n{recommendation}")
    except Exception as e:
        logger.error(f"Error in recommend_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /news <stock_code> command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Format: /news <kode_saham>\nContoh: /news BBCA"
        )
        return
    
    stock_code = context.args[0].upper()
    await update.message.reply_text(f"🔄 Mencari berita {stock_code}...")
    
    try:
        # Get stock info for company name
        stock_data = stock_fetcher.get_stock_info(stock_code)
        company_name = stock_data.get("name", "") if stock_data else ""
        
        # Search news
        news_items = await serper_search.search_stock_news(stock_code, company_name)
        
        if not news_items:
            await update.message.reply_text(
                f"📰 Tidak ada berita terbaru untuk {stock_code}."
            )
            return
        
        # Format and send news
        news_text = serper_search.format_news_summary(news_items)
        await send_long_message(update, news_text)
        
        # Get sentiment analysis
        headlines = serper_search.extract_headlines(news_items)
        if headlines:
            sentiment = await gemini_ai.analyze_sentiment(headlines)
            await send_long_message(update, f"🧠 Sentiment Analysis:\n\n{sentiment}")
    except Exception as e:
        logger.error(f"Error in news_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask <question> command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Format: /ask <pertanyaan>\nContoh: /ask apa itu P/E ratio?"
        )
        return
    
    question = " ".join(context.args)
    await update.message.reply_text(f"🤔 Memikirkan jawaban...")
    
    try:
        # Get AI answer
        answer = await gemini_ai.answer_question(question)
        
        await send_long_message(update, f"💡 Jawaban:\n\n{answer}")
    except Exception as e:
        logger.error(f"Error in ask_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /portfolio command"""
    user_id = update.effective_user.id
    holdings = portfolio_manager.get_portfolio(user_id)
    
    # Get current prices for P/L calculation
    current_prices = {}
    for stock in holdings.keys():
        stock_data = stock_fetcher.get_stock_info(stock)
        if stock_data:
            current_prices[stock] = stock_data["current_price"]
    
    portfolio_text = portfolio_manager.format_portfolio(holdings, current_prices)
    await update.message.reply_text(portfolio_text, parse_mode="Markdown")


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy <code> <qty> <price> command"""
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Format: `/buy <kode> <qty> <harga>`\nContoh: `/buy BBCA 100 9500`",
            parse_mode="Markdown"
        )
        return
    
    try:
        stock_code = context.args[0].upper()
        quantity = int(context.args[1])
        price = float(context.args[2])
        
        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive")
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Format salah. Contoh: `/buy BBCA 100 9500`",
            parse_mode="Markdown"
        )
        return
    
    user_id = update.effective_user.id
    result = portfolio_manager.add_buy(user_id, stock_code, quantity, price)
    
    await update.message.reply_text(
        f"✅ **Pembelian Dicatat!**\n\n"
        f"📊 Saham: {stock_code}\n"
        f"📦 Qty: {quantity:,} lot\n"
        f"💰 Harga: Rp {price:,.0f}\n"
        f"💵 Total: Rp {quantity * price:,.0f}\n\n"
        f"📈 Total holding: {result['quantity']:,} lot @ Rp {result['avg_price']:,.0f}",
        parse_mode="Markdown"
    )


async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sell <code> <qty> <price> command"""
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Format: `/sell <kode> <qty> <harga>`\nContoh: `/sell BBCA 50 10000`",
            parse_mode="Markdown"
        )
        return
    
    try:
        stock_code = context.args[0].upper()
        quantity = int(context.args[1])
        price = float(context.args[2])
        
        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive")
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Format salah. Contoh: `/sell BBCA 50 10000`",
            parse_mode="Markdown"
        )
        return
    
    user_id = update.effective_user.id
    result = portfolio_manager.add_sell(user_id, stock_code, quantity, price)
    
    if not result:
        await update.message.reply_text(
            f"❌ Tidak bisa menjual. Pastikan kamu punya cukup {stock_code}.",
            parse_mode="Markdown"
        )
        return
    
    profit_emoji = "🟢" if result["profit"] >= 0 else "🔴"
    
    await update.message.reply_text(
        f"✅ **Penjualan Dicatat!**\n\n"
        f"📊 Saham: {stock_code}\n"
        f"📦 Qty: {quantity:,} lot\n"
        f"💰 Harga jual: Rp {price:,.0f}\n"
        f"💵 Total: Rp {quantity * price:,.0f}\n\n"
        f"{profit_emoji} Profit/Loss: Rp {result['profit']:+,.0f} ({result['profit_pct']:+.2f}%)\n"
        f"📈 Sisa holding: {result['remaining_quantity']:,} lot",
        parse_mode="Markdown"
    )


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alert <code> <above/below> <price> command"""
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Format: `/alert <kode> <above/below> <harga>`\n"
            "Contoh: `/alert BBCA above 10000`",
            parse_mode="Markdown"
        )
        return
    
    try:
        stock_code = context.args[0].upper()
        alert_type = context.args[1].lower()
        target_price = float(context.args[2])
        
        if alert_type not in ["above", "below"]:
            raise ValueError("Alert type must be 'above' or 'below'")
        
        if target_price <= 0:
            raise ValueError("Price must be positive")
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Format salah. Contoh: `/alert BBCA above 10000`",
            parse_mode="Markdown"
        )
        return
    
    user_id = update.effective_user.id
    alert = alert_manager.create_alert(user_id, stock_code, alert_type, target_price)
    
    direction = "naik di atas" if alert_type == "above" else "turun di bawah"
    
    await update.message.reply_text(
        f"🔔 **Alert Created!**\n\n"
        f"📊 Saham: {stock_code}\n"
        f"🎯 Alert ketika harga {direction} Rp {target_price:,.0f}\n"
        f"🆔 ID: `{alert['id']}`",
        parse_mode="Markdown"
    )


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alerts command"""
    user_id = update.effective_user.id
    alerts = alert_manager.get_user_alerts(user_id)
    
    alerts_text = alert_manager.format_alerts(alerts)
    await update.message.reply_text(alerts_text, parse_mode="Markdown")


async def delete_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /deletealert <id> command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Format: `/deletealert <alert_id>`",
            parse_mode="Markdown"
        )
        return
    
    alert_id = context.args[0]
    user_id = update.effective_user.id
    
    if alert_manager.delete_alert(user_id, alert_id):
        await update.message.reply_text(
            f"✅ Alert `{alert_id}` telah dihapus.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Alert `{alert_id}` tidak ditemukan.",
            parse_mode="Markdown"
        )


async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /market command for general market overview"""
    await update.message.reply_text("🔄 Mengambil data pasar...", parse_mode="Markdown")
    
    # Get market news
    market_news = await serper_search.search_market_news()
    news_text = serper_search.format_news_summary(market_news, max_items=5)
    
    await update.message.reply_text(
        f"📈 **UPDATE PASAR INDONESIA**\n━━━━━━━━━━━━━━━━━━━━━━\n\n{news_text}",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    text = update.message.text
    
    # Treat as a question if it's a normal message
    await update.message.reply_text("🤔 Memikirkan jawaban...")
    
    try:
        answer = await gemini_ai.answer_question(text)
        await send_long_message(update, f"💡 {answer}")
    except Exception as e:
        logger.error(f"Error in handle_message: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


# ============== NEW ADVANCED ANALYSIS COMMANDS ==============

async def ta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ta <stock_code> - Technical Analysis"""
    if not context.args:
        await update.message.reply_text(
            "❌ Format: /ta <kode_saham>\nContoh: /ta BBCA"
        )
        return
    
    stock_code = context.args[0].upper()
    await update.message.reply_text(f"📊 Menghitung indikator teknikal {stock_code}...")
    
    try:
        ta_data = technical_analysis.get_technical_indicators(stock_code)
        
        if not ta_data:
            await update.message.reply_text(f"❌ Data teknikal untuk {stock_code} tidak tersedia.")
            return
        
        result = technical_analysis.format_technical_analysis(ta_data)
        await send_long_message(update, result)
        
    except Exception as e:
        logger.error(f"Error in ta_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compare <stock1> <stock2> - Compare two stocks"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format: /compare <kode1> <kode2>\nContoh: /compare BBCA BBRI"
        )
        return
    
    stock1 = context.args[0].upper()
    stock2 = context.args[1].upper()
    await update.message.reply_text(f"📊 Membandingkan {stock1} vs {stock2}...")
    
    try:
        data1 = stock_fetcher.get_stock_info(stock1)
        data2 = stock_fetcher.get_stock_info(stock2)
        
        if not data1:
            await update.message.reply_text(f"❌ Saham {stock1} tidak ditemukan.")
            return
        if not data2:
            await update.message.reply_text(f"❌ Saham {stock2} tidak ditemukan.")
            return
        
        def safe_val(val, default=0):
            return val if val is not None else default
        
        # Format comparison
        comparison = f"""
📊 PERBANDINGAN SAHAM
━━━━━━━━━━━━━━━━━━━━━━

        {stock1}  vs  {stock2}
━━━━━━━━━━━━━━━━━━━━━━

💰 Harga:
   {stock1}: Rp {safe_val(data1.get('current_price')):,.0f}
   {stock2}: Rp {safe_val(data2.get('current_price')):,.0f}

📈 Perubahan:
   {stock1}: {safe_val(data1.get('price_change_pct')):+.2f}%
   {stock2}: {safe_val(data2.get('price_change_pct')):+.2f}%

📊 P/E Ratio:
   {stock1}: {safe_val(data1.get('pe_ratio'), 'N/A')}
   {stock2}: {safe_val(data2.get('pe_ratio'), 'N/A')}

📊 P/B Ratio:
   {stock1}: {safe_val(data1.get('pb_ratio'), 'N/A')}
   {stock2}: {safe_val(data2.get('pb_ratio'), 'N/A')}

💵 Dividend Yield:
   {stock1}: {safe_val(data1.get('dividend_yield', 0))*100:.2f}%
   {stock2}: {safe_val(data2.get('dividend_yield', 0))*100:.2f}%

🏢 Market Cap:
   {stock1}: Rp {safe_val(data1.get('market_cap'))/1e12:.2f}T
   {stock2}: Rp {safe_val(data2.get('market_cap'))/1e12:.2f}T

🏭 Sektor:
   {stock1}: {data1.get('sector', 'N/A')}
   {stock2}: {data2.get('sector', 'N/A')}
"""
        await send_long_message(update, comparison)
        
        # Get AI comparison
        prompt = f"Bandingkan saham {stock1} vs {stock2} berdasarkan data yang ada. Mana yang lebih baik untuk investasi?"
        ai_analysis = await gemini_ai.answer_question(prompt)
        await send_long_message(update, f"🤖 AI Analysis:\n\n{ai_analysis}")
        
    except Exception as e:
        logger.error(f"Error in compare_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def screener_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /screener <type> - Screen stocks"""
    valid_types = ["lowpe", "dividend", "lowpb", "gainers", "losers"]
    
    if not context.args:
        await update.message.reply_text(
            "📊 STOCK SCREENER\n\n"
            "Pilih tipe screener:\n"
            "• /screener lowpe - P/E < 15\n"
            "• /screener dividend - Dividend > 3%\n"
            "• /screener lowpb - P/B < 1.5\n"
            "• /screener gainers - Top 5 Naik\n"
            "• /screener losers - Top 5 Turun"
        )
        return
    
    screen_type = context.args[0].lower()
    
    if screen_type not in valid_types:
        await update.message.reply_text(f"❌ Tipe tidak valid. Pilih: {', '.join(valid_types)}")
        return
    
    await update.message.reply_text(f"🔍 Scanning saham ({screen_type})... Ini mungkin memakan waktu.")
    
    try:
        if screen_type == "lowpe":
            results = stock_screener.screen_by_pe(max_pe=15)
            title = "LOW P/E STOCKS (P/E < 15)"
        elif screen_type == "dividend":
            results = stock_screener.screen_by_dividend(min_yield=0.03)
            title = "HIGH DIVIDEND STOCKS (Yield > 3%)"
        elif screen_type == "lowpb":
            results = stock_screener.screen_by_pb(max_pb=1.5)
            title = "LOW P/B STOCKS (P/B < 1.5)"
        elif screen_type == "gainers":
            results = stock_screener.screen_top_gainers(limit=5)
            title = "TOP 5 GAINERS"
        elif screen_type == "losers":
            results = stock_screener.screen_top_losers(limit=5)
            title = "TOP 5 LOSERS"
        
        formatted = stock_screener.format_screener_results(results, title)
        await send_long_message(update, formatted)
        
    except Exception as e:
        logger.error(f"Error in screener_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /watchlist - Manage watchlist"""
    user_id = update.effective_user.id
    
    if not context.args:
        # Show watchlist
        stocks = watchlist_manager.get_watchlist(user_id)
        
        if not stocks:
            await update.message.reply_text(
                "📋 Watchlist kosong.\n\n"
                "Tambah saham: /watchlist add BBCA\n"
                "Hapus saham: /watchlist remove BBCA"
            )
            return
        
        await update.message.reply_text(f"🔄 Mengambil data {len(stocks)} saham...")
        
        lines = ["📋 WATCHLIST KAMU", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        for stock in stocks:
            data = stock_fetcher.get_stock_info(stock)
            if data:
                change = data.get('price_change_pct', 0) or 0
                emoji = "🟢" if change >= 0 else "🔴"
                lines.append(f"{emoji} {stock}: Rp {data.get('current_price', 0):,.0f} ({change:+.2f}%)")
            else:
                lines.append(f"⚪ {stock}: Data tidak tersedia")
        
        lines.append("")
        lines.append("Tambah: /watchlist add <kode>")
        lines.append("Hapus: /watchlist remove <kode>")
        
        await update.message.reply_text("\n".join(lines))
        return
    
    action = context.args[0].lower()
    
    if action == "add" and len(context.args) >= 2:
        stock_code = context.args[1].upper()
        if watchlist_manager.add_stock(user_id, stock_code):
            await update.message.reply_text(f"✅ {stock_code} ditambahkan ke watchlist.")
        else:
            await update.message.reply_text(f"⚠️ {stock_code} sudah ada di watchlist.")
    
    elif action == "remove" and len(context.args) >= 2:
        stock_code = context.args[1].upper()
        if watchlist_manager.remove_stock(user_id, stock_code):
            await update.message.reply_text(f"✅ {stock_code} dihapus dari watchlist.")
        else:
            await update.message.reply_text(f"⚠️ {stock_code} tidak ada di watchlist.")
    
    elif action == "clear":
        watchlist_manager.clear_watchlist(user_id)
        await update.message.reply_text("✅ Watchlist dikosongkan.")
    
    else:
        await update.message.reply_text(
            "📋 WATCHLIST COMMANDS\n\n"
            "/watchlist - Lihat watchlist\n"
            "/watchlist add BBCA - Tambah saham\n"
            "/watchlist remove BBCA - Hapus saham\n"
            "/watchlist clear - Kosongkan semua"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}\n{traceback.format_exc()}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Terjadi kesalahan. Silakan coba lagi nanti."
        )


# ============== NEW PHASE 1 COMMANDS ==============

async def ihsg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ihsg command - IHSG index data"""
    await update.message.reply_text("📊 Mengambil data IHSG...")
    
    try:
        ihsg_data = market_data_fetcher.get_ihsg_data()
        
        if not ihsg_data:
            await update.message.reply_text("❌ Data IHSG tidak tersedia saat ini.")
            return
        
        result = market_data_fetcher.format_ihsg_summary(ihsg_data)
        await send_long_message(update, result)
        
    except Exception as e:
        logger.error(f"Error in ihsg_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def kurs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kurs command - Currency exchange rates"""
    await update.message.reply_text("💱 Mengambil data kurs...")
    
    try:
        if context.args:
            # Get specific currency
            pair = context.args[0].upper()
            if "/" not in pair:
                pair = f"{pair}/IDR"
            
            rate = market_data_fetcher.get_single_currency(pair)
            if rate:
                emoji = "🟢" if rate["change"] >= 0 else "🔴"
                result = f"💱 {rate['pair']}\n\n"
                result += f"💰 Rate: Rp {rate['rate']:,.2f}\n"
                result += f"{emoji} Change: {rate['change']:+,.2f} ({rate['change_pct']:+.2f}%)"
                await update.message.reply_text(result)
            else:
                await update.message.reply_text(f"❌ Kurs {pair} tidak ditemukan.")
        else:
            # Get all currencies
            rates = market_data_fetcher.get_currency_rates()
            result = market_data_fetcher.format_currency_summary(rates)
            await send_long_message(update, result)
        
    except Exception as e:
        logger.error(f"Error in kurs_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command - Transaction history"""
    user_id = update.effective_user.id
    
    limit = 10
    if context.args:
        try:
            limit = int(context.args[0])
            limit = min(limit, 20)  # Max 20
        except ValueError:
            pass
    
    transactions = portfolio_manager.get_transactions(user_id, limit)
    result = portfolio_manager.format_transactions(transactions)
    await send_long_message(update, result)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command - Show interactive menu"""
    keyboard = [
        [
            InlineKeyboardButton("📊 IHSG", callback_data="menu_ihsg"),
            InlineKeyboardButton("💱 Kurs", callback_data="menu_kurs"),
        ],
        [
            InlineKeyboardButton("💼 Portfolio", callback_data="menu_portfolio"),
            InlineKeyboardButton("📋 History", callback_data="menu_history"),
        ],
        [
            InlineKeyboardButton("🔔 Alerts", callback_data="menu_alerts"),
            InlineKeyboardButton("📋 Watchlist", callback_data="menu_watchlist"),
        ],
        [
            InlineKeyboardButton("📊 Screener", callback_data="menu_screener"),
            InlineKeyboardButton("📰 Market News", callback_data="menu_market"),
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 AI Financial Advisor\n\n"
        "Pilih menu di bawah atau ketik perintah langsung:",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_ihsg":
        await query.message.reply_text("📊 Mengambil data IHSG...")
        ihsg_data = market_data_fetcher.get_ihsg_data()
        if ihsg_data:
            result = market_data_fetcher.format_ihsg_summary(ihsg_data)
            await query.message.reply_text(result)
        else:
            await query.message.reply_text("❌ Data IHSG tidak tersedia")
    
    elif data == "menu_kurs":
        await query.message.reply_text("💱 Mengambil data kurs...")
        rates = market_data_fetcher.get_currency_rates()
        result = market_data_fetcher.format_currency_summary(rates)
        await query.message.reply_text(result)
    
    elif data == "menu_portfolio":
        user_id = query.from_user.id
        holdings = portfolio_manager.get_portfolio(user_id)
        current_prices = {}
        for stock in holdings.keys():
            stock_data = stock_fetcher.get_stock_info(stock)
            if stock_data:
                current_prices[stock] = stock_data["current_price"]
        result = portfolio_manager.format_portfolio(holdings, current_prices)
        await query.message.reply_text(result)
    
    elif data == "menu_history":
        user_id = query.from_user.id
        transactions = portfolio_manager.get_transactions(user_id, 10)
        result = portfolio_manager.format_transactions(transactions)
        await query.message.reply_text(result)
    
    elif data == "menu_alerts":
        user_id = query.from_user.id
        alerts = alert_manager.get_user_alerts(user_id)
        result = alert_manager.format_alerts(alerts)
        await query.message.reply_text(result)
    
    elif data == "menu_watchlist":
        user_id = query.from_user.id
        stocks = watchlist_manager.get_watchlist(user_id)
        if not stocks:
            await query.message.reply_text("📋 Watchlist kosong.\n\nTambah: /watchlist add BBCA")
        else:
            lines = ["📋 WATCHLIST KAMU", ""]
            for stock in stocks:
                lines.append(f"• {stock}")
            lines.append("\nLihat detail: /watchlist")
            await query.message.reply_text("\n".join(lines))
    
    elif data == "menu_screener":
        keyboard = [
            [
                InlineKeyboardButton("📉 Low P/E", callback_data="screen_lowpe"),
                InlineKeyboardButton("💰 Dividend", callback_data="screen_dividend"),
            ],
            [
                InlineKeyboardButton("🟢 Gainers", callback_data="screen_gainers"),
                InlineKeyboardButton("🔴 Losers", callback_data="screen_losers"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("📊 Pilih tipe screener:", reply_markup=reply_markup)
    
    elif data == "menu_market":
        await query.message.reply_text("📰 Mengambil berita pasar...")
        market_news = await serper_search.search_market_news()
        news_text = serper_search.format_news_summary(market_news, max_items=5)
        await query.message.reply_text(f"📈 UPDATE PASAR INDONESIA\n━━━━━━━━━━━━━━━━━━━━━━\n\n{news_text}")
    
    # Screener callbacks
    elif data.startswith("screen_"):
        screen_type = data.replace("screen_", "")
        await query.message.reply_text(f"🔍 Scanning saham...")
        
        try:
            if screen_type == "lowpe":
                results = stock_screener.screen_by_pe(max_pe=15)
                title = "LOW P/E STOCKS"
            elif screen_type == "dividend":
                results = stock_screener.screen_by_dividend(min_yield=0.03)
                title = "HIGH DIVIDEND STOCKS"
            elif screen_type == "gainers":
                results = stock_screener.screen_top_gainers(limit=5)
                title = "TOP 5 GAINERS"
            elif screen_type == "losers":
                results = stock_screener.screen_top_losers(limit=5)
                title = "TOP 5 LOSERS"
            else:
                results = []
                title = "SCREENER"
            
            formatted = stock_screener.format_screener_results(results, title)
            await query.message.reply_text(formatted)
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")


# ============== PHASE 2: VISUALIZATION COMMANDS ==============

async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chart <stock_code> [period] [type] command"""
    if not context.args:
        await update.message.reply_text(
            "📈 CHART GENERATOR\n\n"
            "Format: /chart <kode> [periode] [tipe]\n\n"
            "Periode: 1d, 5d, 1mo, 3mo, 6mo, 1y (default: 1mo)\n"
            "Tipe: candle, line (default: candle)\n\n"
            "Contoh:\n"
            "• /chart BBCA\n"
            "• /chart BBCA 3mo\n"
            "• /chart BBCA 1mo line"
        )
        return
    
    stock_code = context.args[0].upper()
    period = context.args[1].lower() if len(context.args) > 1 else "1mo"
    chart_type = context.args[2].lower() if len(context.args) > 2 else "candle"
    
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
    if period not in valid_periods:
        period = "1mo"
    
    await update.message.reply_text(f"📊 Generating {chart_type} chart for {stock_code}...")
    
    try:
        if chart_type == "line":
            chart_buf = chart_generator.generate_line_chart(stock_code, period)
        else:
            chart_buf = chart_generator.generate_candlestick_chart(stock_code, period)
        
        if chart_buf:
            await update.message.reply_photo(
                photo=chart_buf,
                caption=f"📈 {stock_code} - {period.upper()} ({chart_type.capitalize()} Chart)"
            )
        else:
            await update.message.reply_text(f"❌ Gagal generate chart untuk {stock_code}")
            
    except Exception as e:
        logger.error(f"Error in chart_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def sector_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sector command - Sector performance"""
    await update.message.reply_text("📊 Menghitung performa sektor... (ini mungkin memakan waktu)")
    
    try:
        sector_perf = market_data_fetcher.get_sector_performance()
        
        if not sector_perf:
            await update.message.reply_text("❌ Data sektor tidak tersedia saat ini.")
            return
        
        # Send text summary
        result = market_data_fetcher.format_sector_performance(sector_perf)
        await send_long_message(update, result)
        
        # Generate and send chart
        chart_buf = chart_generator.generate_sector_performance_chart(sector_perf)
        if chart_buf:
            await update.message.reply_photo(
                photo=chart_buf,
                caption="📊 Sector Performance Chart"
            )
        
    except Exception as e:
        logger.error(f"Error in sector_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def comparechart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /comparechart <stock1> <stock2> [period] command"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "📊 COMPARISON CHART\n\n"
            "Format: /comparechart <kode1> <kode2> [periode]\n\n"
            "Contoh:\n"
            "• /comparechart BBCA BBRI\n"
            "• /comparechart BBCA BBRI BMRI 3mo"
        )
        return
    
    # Get stock codes (max 5)
    stocks = [arg.upper() for arg in context.args if not any(c.isdigit() for c in arg)][:5]
    
    # Get period if specified
    period = "1mo"
    for arg in context.args:
        if arg.lower() in ["1d", "5d", "1mo", "3mo", "6mo", "1y"]:
            period = arg.lower()
            break
    
    await update.message.reply_text(f"📊 Generating comparison chart for {', '.join(stocks)}...")
    
    try:
        chart_buf = chart_generator.generate_comparison_chart(stocks, period)
        
        if chart_buf:
            await update.message.reply_photo(
                photo=chart_buf,
                caption=f"📈 Stock Comparison: {' vs '.join(stocks)} - {period.upper()}"
            )
        else:
            await update.message.reply_text("❌ Gagal generate comparison chart")
            
    except Exception as e:
        logger.error(f"Error in comparechart_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


# ============== PHASE 3: NOTIFICATION COMMANDS ==============

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command - Manage notification subscriptions"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not context.args:
        # Show subscription status
        subs = notification_manager.get_user_subscriptions(user_id)
        status = notification_manager.format_subscription_status(subs)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Daily Summary" if not subs["daily_summary"] else "❌ Daily Summary",
                    callback_data="sub_daily"
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ Breaking News" if not subs["breaking_news"] else "❌ Breaking News", 
                    callback_data="sub_news"
                ),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status + "\n\nKlik tombol untuk toggle:",
            reply_markup=reply_markup
        )
        return
    
    action = context.args[0].lower()
    
    if action == "daily":
        notification_manager.subscribe_daily_summary(user_id, chat_id)
        await update.message.reply_text(
            "✅ Berhasil subscribe ke Daily Summary!\n"
            "Kamu akan menerima ringkasan pasar setiap jam 17:00 WIB (Senin-Jumat)"
        )
    elif action == "news":
        notification_manager.subscribe_breaking_news(user_id, chat_id)
        await update.message.reply_text("✅ Berhasil subscribe ke Breaking News!")
    elif action == "earnings":
        notification_manager.subscribe_earnings(user_id, chat_id)
        await update.message.reply_text("✅ Berhasil subscribe ke Earnings Alerts!")
    else:
        await update.message.reply_text(
            "📬 SUBSCRIBE OPTIONS\n\n"
            "/subscribe daily - Ringkasan harian (17:00)\n"
            "/subscribe news - Berita penting\n"
            "/subscribe earnings - Alert laporan keuangan"
        )


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe command"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "📭 UNSUBSCRIBE OPTIONS\n\n"
            "/unsubscribe daily - Berhenti ringkasan harian\n"
            "/unsubscribe news - Berhenti berita penting\n"
            "/unsubscribe earnings - Berhenti earnings alert\n"
            "/unsubscribe all - Berhenti semua"
        )
        return
    
    action = context.args[0].lower()
    
    if action == "daily":
        notification_manager.unsubscribe_daily_summary(user_id)
        await update.message.reply_text("✅ Berhasil unsubscribe dari Daily Summary")
    elif action == "news":
        notification_manager.unsubscribe_breaking_news(user_id)
        await update.message.reply_text("✅ Berhasil unsubscribe dari Breaking News")
    elif action == "earnings":
        notification_manager.unsubscribe_earnings(user_id)
        await update.message.reply_text("✅ Berhasil unsubscribe dari Earnings Alerts")
    elif action == "all":
        notification_manager.unsubscribe_daily_summary(user_id)
        notification_manager.unsubscribe_breaking_news(user_id)
        notification_manager.unsubscribe_earnings(user_id)
        await update.message.reply_text("✅ Berhasil unsubscribe dari semua notifikasi")
    else:
        await update.message.reply_text("❌ Opsi tidak valid")


# ============== PHASE 4: PORTFOLIO PRO COMMANDS ==============

async def diversify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /diversify command - Portfolio diversification analysis"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("📊 Menganalisis diversifikasi portfolio...")
    
    try:
        # Get user's portfolio
        holdings = portfolio_manager.get_portfolio(user_id)
        
        if not holdings:
            await update.message.reply_text(
                "❌ Portfolio kosong!\n\n"
                "Tambahkan saham dulu dengan /buy <kode> <jumlah> <harga>"
            )
            return
        
        # Get current stock info
        stock_info = {}
        for stock in holdings.keys():
            data = stock_fetcher.get_stock_info(stock)
            if data:
                stock_info[stock] = {
                    "current_price": data["current_price"],
                    "sector": data.get("sector", "Unknown")
                }
        
        # Analyze diversification
        analysis = portfolio_analyzer.analyze_diversification(holdings, stock_info)
        
        # Format and send text result
        result = portfolio_analyzer.format_diversification_analysis(analysis)
        await send_long_message(update, result)
        
        # Generate and send chart
        chart_buf = portfolio_analyzer.generate_allocation_chart(analysis)
        if chart_buf:
            await update.message.reply_photo(
                photo=chart_buf,
                caption="📊 Portfolio Allocation Chart"
            )
        
    except Exception as e:
        logger.error(f"Error in diversify_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command - Export portfolio to PDF/Excel"""
    user_id = update.effective_user.id
    
    export_format = "excel"
    if context.args:
        export_format = context.args[0].lower()
    
    if export_format not in ["excel", "pdf"]:
        await update.message.reply_text(
            "📤 EXPORT PORTFOLIO\n\n"
            "/export excel - Download as Excel file\n"
            "/export pdf - Download as PDF file"
        )
        return
    
    await update.message.reply_text(f"📤 Generating {export_format.upper()} file...")
    
    try:
        # Get user's portfolio and transactions
        holdings = portfolio_manager.get_portfolio(user_id)
        transactions = portfolio_manager.get_transactions(user_id, 50)
        
        if not holdings:
            await update.message.reply_text("❌ Portfolio kosong!")
            return
        
        # Get current stock info
        stock_info = {}
        for stock in holdings.keys():
            data = stock_fetcher.get_stock_info(stock)
            if data:
                stock_info[stock] = {
                    "current_price": data["current_price"],
                    "sector": data.get("sector", "Unknown")
                }
        
        # Get analysis for PDF
        analysis = portfolio_analyzer.analyze_diversification(holdings, stock_info)
        
        if export_format == "excel":
            file_buf = portfolio_analyzer.export_to_excel(holdings, transactions, stock_info)
            filename = f"portfolio_{user_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        else:
            file_buf = portfolio_analyzer.export_to_pdf(holdings, transactions, stock_info, analysis)
            filename = f"portfolio_{user_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        if file_buf:
            await update.message.reply_document(
                document=file_buf,
                filename=filename,
                caption=f"📊 Portfolio Report - {datetime.now().strftime('%Y-%m-%d')}"
            )
        else:
            await update.message.reply_text("❌ Gagal generate file")
        
    except Exception as e:
        logger.error(f"Error in export_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


# ============== PHASE 5: AI PRO COMMANDS ==============

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command - Manage user investment profile"""
    user_id = update.effective_user.id
    
    if not context.args:
        # Show current profile
        profile = user_profile_manager.get_user_profile(user_id)
        result = user_profile_manager.format_profile(profile)
        
        keyboard = [
            [
                InlineKeyboardButton("🛡️ Konservatif", callback_data="profile_conservative"),
                InlineKeyboardButton("⚖️ Moderat", callback_data="profile_moderate"),
                InlineKeyboardButton("🚀 Agresif", callback_data="profile_aggressive"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            result + "\n\nPilih profil risiko:",
            reply_markup=reply_markup
        )
        return
    
    action = context.args[0].lower()
    
    if action in ["conservative", "moderate", "aggressive", "konservatif", "moderat", "agresif"]:
        # Map Indonesian names
        if action == "konservatif":
            action = "conservative"
        elif action == "moderat":
            action = "moderate"
        elif action == "agresif":
            action = "aggressive"
        
        user_profile_manager.set_risk_profile(user_id, action)
        risk_info = user_profile_manager.RISK_PROFILES[action]
        await update.message.reply_text(
            f"✅ Profil risiko diubah ke {risk_info['emoji']} {risk_info['name']}\n\n"
            f"{risk_info['description']}"
        )
    elif action == "goal" and len(context.args) > 1:
        goals = context.args[1:]
        user_profile_manager.set_investment_goals(user_id, goals)
        await update.message.reply_text(f"✅ Tujuan investasi diupdate: {', '.join(goals)}")
    elif action == "sector" and len(context.args) > 1:
        sectors = context.args[1:]
        user_profile_manager.set_preferred_sectors(user_id, sectors)
        await update.message.reply_text(f"✅ Sektor favorit diupdate: {', '.join(sectors)}")
    else:
        await update.message.reply_text(
            "👤 PROFILE COMMANDS\n\n"
            "/profile - Lihat profil saat ini\n"
            "/profile conservative - Set profil konservatif\n"
            "/profile moderate - Set profil moderat\n"
            "/profile aggressive - Set profil agresif\n"
            "/profile goal <goals> - Set tujuan investasi\n"
            "/profile sector <sectors> - Set sektor favorit"
        )


async def advice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /advice command - Get personalized investment advice"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("🤖 Menganalisis profil dan portfolio kamu...")
    
    try:
        # Get user profile context
        user_context = user_profile_manager.get_conversation_context(user_id)
        
        # Get portfolio data
        holdings = portfolio_manager.get_portfolio(user_id)
        if holdings:
            portfolio_lines = []
            for stock, data in holdings.items():
                portfolio_lines.append(f"- {stock}: {data['quantity']} lot @ Rp {data['avg_price']:,.0f}")
            portfolio_data = "\n".join(portfolio_lines)
        else:
            portfolio_data = "Portfolio kosong"
        
        # Get market data
        ihsg_data = market_data_fetcher.get_ihsg_data()
        market_data = f"IHSG: {ihsg_data['value']:,.2f} ({ihsg_data['change_pct']:+.2f}%)" if ihsg_data else "Data market tidak tersedia"
        
        # Get personalized advice from AI
        advice = await gemini_ai.get_personalized_advice(user_context, portfolio_data, market_data)
        
        # Save conversation
        user_profile_manager.add_conversation(user_id, "Minta saran investasi", advice[:200])
        
        await send_long_message(update, f"🎯 SARAN PERSONAL\n━━━━━━━━━━━━━━━━━━━━━━\n\n{advice}")
        
    except Exception as e:
        logger.error(f"Error in advice_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /predict <stock_code> command - AI market prediction"""
    if not context.args:
        await update.message.reply_text(
            "🔮 MARKET PREDICTION\n\n"
            "Format: /predict <kode_saham>\n"
            "Contoh: /predict BBCA"
        )
        return
    
    stock_code = context.args[0].upper()
    await update.message.reply_text(f"🔮 Generating prediction untuk {stock_code}...")
    
    try:
        # Get stock data
        stock_data = stock_fetcher.get_stock_info(stock_code)
        if not stock_data:
            await update.message.reply_text(f"❌ Saham {stock_code} tidak ditemukan")
            return
        
        # Get technical analysis
        ta_result = technical_analysis.get_technical_indicators(stock_code)
        if ta_result:
            ta_text = f"""
RSI: {ta_result.get('rsi', 'N/A')} ({ta_result.get('rsi_signal', 'N/A')})
MACD: {ta_result.get('macd_signal', 'N/A')}
SMA20: {ta_result.get('sma_20', 'N/A')} ({ta_result.get('sma_signal', 'N/A')})
"""
        else:
            ta_text = "Technical analysis tidak tersedia"
        
        # Get news
        news = await serper_search.search_stock_news(stock_code)
        news_summary = serper_search.format_news_summary(news, max_items=3) if news else ""
        
        # Get AI prediction
        prediction = await gemini_ai.predict_market_trend(stock_code, stock_data, ta_text, news_summary)
        
        await send_long_message(update, f"🔮 PREDIKSI {stock_code}\n━━━━━━━━━━━━━━━━━━━━━━\n\n{prediction}")
        
    except Exception as e:
        logger.error(f"Error in predict_command: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}\n{traceback.format_exc()}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Terjadi kesalahan. Silakan coba lagi nanti."
        )


def setup_handlers(application: Application):
    """Register all handlers to the application"""
    
    # Command handlers - Basic
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("recommend", recommend_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("market", market_command))
    
    # Command handlers - Market Data (NEW)
    application.add_handler(CommandHandler("ihsg", ihsg_command))
    application.add_handler(CommandHandler("kurs", kurs_command))
    
    # Command handlers - Portfolio
    application.add_handler(CommandHandler("portfolio", portfolio_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("sell", sell_command))
    application.add_handler(CommandHandler("history", history_command))
    
    # Command handlers - Alerts
    application.add_handler(CommandHandler("alert", alert_command))
    application.add_handler(CommandHandler("alerts", alerts_command))
    application.add_handler(CommandHandler("deletealert", delete_alert_command))
    
    # Command handlers - Advanced Analysis
    application.add_handler(CommandHandler("ta", ta_command))
    application.add_handler(CommandHandler("compare", compare_command))
    application.add_handler(CommandHandler("screener", screener_command))
    application.add_handler(CommandHandler("watchlist", watchlist_command))
    
    # Command handlers - Charts & Visualization (PHASE 2)
    application.add_handler(CommandHandler("chart", chart_command))
    application.add_handler(CommandHandler("sector", sector_command))
    application.add_handler(CommandHandler("comparechart", comparechart_command))
    
    # Command handlers - Notifications (PHASE 3)
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    
    # Command handlers - Portfolio Pro (PHASE 4)
    application.add_handler(CommandHandler("diversify", diversify_command))
    application.add_handler(CommandHandler("export", export_command))
    
    # Command handlers - AI Pro (PHASE 5)
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("advice", advice_command))
    application.add_handler(CommandHandler("predict", predict_command))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    return application
