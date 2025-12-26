"""
AI Financial Advisor - Main Application
Telegram bot for stock analysis and investment advice
"""
import asyncio
import logging
from datetime import datetime
from telegram.ext import Application
from apscheduler.schedulers.background import BackgroundScheduler
import threading

from config.settings import TELEGRAM_BOT_TOKEN, ALERT_CHECK_INTERVAL
from handlers.telegram_handlers import setup_handlers
from modules.stock_data import StockDataFetcher
from modules.alerts import AlertManager
from modules.notifications import NotificationManager
from modules.market_data import MarketData
from modules.portfolio import PortfolioManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize modules
stock_fetcher = StockDataFetcher()
alert_manager = AlertManager()
notification_manager = NotificationManager()
market_data_fetcher = MarketData()
portfolio_manager = PortfolioManager()

# Global application reference for alerts
_application = None


def check_price_alerts_sync():
    """
    Synchronous wrapper for checking price alerts
    Called by the background scheduler
    """
    global _application
    if _application is None:
        return
    
    logger.info("Checking price alerts...")
    
    try:
        # Get all active alerts
        all_alerts = alert_manager.get_all_active_alerts()
        
        for user_id, alerts in all_alerts.items():
            for alert in alerts:
                stock_code = alert["stock"]
                
                # Get current price
                stock_data = stock_fetcher.get_stock_info(stock_code)
                if not stock_data:
                    continue
                
                current_price = stock_data["current_price"]
                
                # Check if alert should trigger
                if alert_manager.check_alert(alert, current_price):
                    # Trigger the alert
                    triggered = alert_manager.trigger_alert(user_id, alert["id"])
                    
                    if triggered:
                        # Send notification to user
                        notification = alert_manager.format_triggered_alert(alert, current_price)
                        
                        try:
                            # Use asyncio to send message
                            asyncio.run(_application.bot.send_message(
                                chat_id=int(user_id),
                                text=notification,
                                parse_mode="Markdown"
                            ))
                            logger.info(f"Alert triggered for user {user_id}: {stock_code}")
                        except Exception as e:
                            logger.error(f"Failed to send alert to user {user_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")


def send_daily_summary_sync():
    """
    Send daily summary to subscribed users at 17:00
    Called by the background scheduler
    """
    global _application
    if _application is None:
        return
    
    logger.info("Sending daily summaries...")
    
    try:
        # Get IHSG data
        ihsg_data = market_data_fetcher.get_ihsg_data()
        
        # Get sector performance
        sector_perf = market_data_fetcher.get_sector_performance()
        
        # Build summary message
        summary_lines = []
        summary_lines.append("📊 DAILY MARKET SUMMARY")
        summary_lines.append(f"📅 {datetime.now().strftime('%d %B %Y')}")
        summary_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        summary_lines.append("")
        
        # IHSG section
        if ihsg_data:
            emoji = "🟢" if ihsg_data["change"] >= 0 else "🔴"
            summary_lines.append(f"📈 IHSG: {ihsg_data['value']:,.2f}")
            summary_lines.append(f"{emoji} {ihsg_data['change']:+,.2f} ({ihsg_data['change_pct']:+.2f}%)")
            summary_lines.append("")
        
        # Sector section
        if sector_perf:
            summary_lines.append("📊 TOP SECTORS:")
            sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
            for sector, perf in sorted_sectors[:3]:
                emoji = "🟢" if perf >= 0 else "🔴"
                summary_lines.append(f"   {emoji} {sector}: {perf:+.2f}%")
            summary_lines.append("")
        
        summary_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        summary_lines.append("Gunakan /menu untuk akses cepat")
        
        summary_message = "\n".join(summary_lines)
        
        # Get subscribers
        subscribers = notification_manager.get_daily_summary_subscribers()
        
        for sub in subscribers:
            try:
                user_id = sub["user_id"]
                chat_id = sub.get("chat_id", user_id)
                
                # Get user's portfolio summary if they have one
                portfolio = portfolio_manager.get_portfolio(user_id)
                
                full_message = summary_message
                
                if portfolio:
                    # Add portfolio value
                    current_prices = {}
                    total_value = 0
                    for stock, data in portfolio.items():
                        stock_data = stock_fetcher.get_stock_info(stock)
                        if stock_data:
                            current_prices[stock] = stock_data["current_price"]
                            total_value += data["quantity"] * stock_data["current_price"]
                    
                    if total_value > 0:
                        full_message += f"\n\n💼 Portfolio Value: Rp {total_value:,.0f}"
                
                asyncio.run(_application.bot.send_message(
                    chat_id=int(chat_id),
                    text=full_message
                ))
                logger.info(f"Daily summary sent to user {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to send daily summary to user {user_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error sending daily summaries: {e}")


def main():
    """Main function to run the bot"""
    global _application
    
    # Validate configuration
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set! Please configure .env file.")
        print("\n❌ ERROR: TELEGRAM_BOT_TOKEN tidak ditemukan!")
        print("📝 Langkah-langkah:")
        print("   1. Copy file .env.example menjadi .env")
        print("   2. Isi TELEGRAM_BOT_TOKEN dengan token dari @BotFather")
        print("   3. Jalankan ulang aplikasi\n")
        return
    
    logger.info("Starting AI Financial Advisor Bot...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    _application = application
    
    # Setup handlers
    setup_handlers(application)
    
    # Setup background scheduler for alerts and daily summary
    scheduler = BackgroundScheduler()
    
    # Alert checker - every minute
    scheduler.add_job(
        check_price_alerts_sync,
        'interval',
        seconds=ALERT_CHECK_INTERVAL,
        id='check_alerts'
    )
    
    # Daily summary - at 17:00 every weekday
    scheduler.add_job(
        send_daily_summary_sync,
        'cron',
        hour=17,
        minute=0,
        day_of_week='mon-fri',
        id='daily_summary'
    )
    
    scheduler.start()
    
    # Start the bot
    logger.info("Bot is running! Press Ctrl+C to stop.")
    print("\n" + "="*50)
    print("🤖 AI Financial Advisor Bot is RUNNING!")
    print("="*50)
    print("\n📱 Buka Telegram dan cari bot kamu")
    print("💬 Kirim /start untuk memulai")
    print("🔔 Daily Summary: 17:00 WIB (Senin-Jumat)")
    print("\n⏹️  Tekan Ctrl+C untuk menghentikan bot\n")
    
    try:
        application.run_polling(allowed_updates=["message", "callback_query"])
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    main()

