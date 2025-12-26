"""
Notifications Module
Handles scheduled notifications, daily summaries, and alerts
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import sys
sys.path.append('..')
from config.settings import DATA_DIR


SUBSCRIPTIONS_FILE = DATA_DIR / "subscriptions.json"


class NotificationManager:
    """Manages user notification subscriptions and preferences"""
    
    def __init__(self):
        self.subscriptions_file = SUBSCRIPTIONS_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create subscriptions file if it doesn't exist"""
        if not self.subscriptions_file.exists():
            self.subscriptions_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load subscriptions from file"""
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save subscriptions to file"""
        with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def subscribe_daily_summary(self, user_id: str, chat_id: str = None) -> bool:
        """
        Subscribe user to daily summary notifications
        
        Args:
            user_id: Telegram user ID
            chat_id: Chat ID for sending messages
            
        Returns:
            True if subscribed successfully
        """
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            data[user_id] = {
                "daily_summary": False,
                "breaking_news": False,
                "earnings_alerts": False,
                "chat_id": chat_id or user_id,
                "created_at": datetime.now().isoformat()
            }
        
        data[user_id]["daily_summary"] = True
        data[user_id]["chat_id"] = chat_id or data[user_id].get("chat_id", user_id)
        self._save_data(data)
        return True
    
    def unsubscribe_daily_summary(self, user_id: str) -> bool:
        """Unsubscribe user from daily summary"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id in data:
            data[user_id]["daily_summary"] = False
            self._save_data(data)
        return True
    
    def subscribe_breaking_news(self, user_id: str, chat_id: str = None) -> bool:
        """Subscribe user to breaking news alerts"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            data[user_id] = {
                "daily_summary": False,
                "breaking_news": False,
                "earnings_alerts": False,
                "chat_id": chat_id or user_id,
                "created_at": datetime.now().isoformat()
            }
        
        data[user_id]["breaking_news"] = True
        data[user_id]["chat_id"] = chat_id or data[user_id].get("chat_id", user_id)
        self._save_data(data)
        return True
    
    def unsubscribe_breaking_news(self, user_id: str) -> bool:
        """Unsubscribe user from breaking news"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id in data:
            data[user_id]["breaking_news"] = False
            self._save_data(data)
        return True
    
    def subscribe_earnings(self, user_id: str, chat_id: str = None) -> bool:
        """Subscribe user to earnings alerts"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            data[user_id] = {
                "daily_summary": False,
                "breaking_news": False,
                "earnings_alerts": False,
                "chat_id": chat_id or user_id,
                "created_at": datetime.now().isoformat()
            }
        
        data[user_id]["earnings_alerts"] = True
        data[user_id]["chat_id"] = chat_id or data[user_id].get("chat_id", user_id)
        self._save_data(data)
        return True
    
    def unsubscribe_earnings(self, user_id: str) -> bool:
        """Unsubscribe user from earnings alerts"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id in data:
            data[user_id]["earnings_alerts"] = False
            self._save_data(data)
        return True
    
    def get_user_subscriptions(self, user_id: str) -> Dict[str, Any]:
        """Get user's subscription status"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            return {
                "daily_summary": False,
                "breaking_news": False,
                "earnings_alerts": False
            }
        
        return {
            "daily_summary": data[user_id].get("daily_summary", False),
            "breaking_news": data[user_id].get("breaking_news", False),
            "earnings_alerts": data[user_id].get("earnings_alerts", False)
        }
    
    def get_daily_summary_subscribers(self) -> List[Dict[str, str]]:
        """Get all users subscribed to daily summary"""
        data = self._load_data()
        subscribers = []
        
        for user_id, info in data.items():
            if info.get("daily_summary", False):
                subscribers.append({
                    "user_id": user_id,
                    "chat_id": info.get("chat_id", user_id)
                })
        
        return subscribers
    
    def get_breaking_news_subscribers(self) -> List[Dict[str, str]]:
        """Get all users subscribed to breaking news"""
        data = self._load_data()
        subscribers = []
        
        for user_id, info in data.items():
            if info.get("breaking_news", False):
                subscribers.append({
                    "user_id": user_id,
                    "chat_id": info.get("chat_id", user_id)
                })
        
        return subscribers
    
    def format_subscription_status(self, subs: Dict[str, bool]) -> str:
        """Format subscription status"""
        lines = ["🔔 STATUS LANGGANAN", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        daily_emoji = "✅" if subs.get("daily_summary") else "❌"
        news_emoji = "✅" if subs.get("breaking_news") else "❌"
        earnings_emoji = "✅" if subs.get("earnings_alerts") else "❌"
        
        lines.append(f"{daily_emoji} Daily Summary (17:00)")
        lines.append(f"{news_emoji} Breaking News")
        lines.append(f"{earnings_emoji} Earnings Alerts")
        lines.append("")
        lines.append("Gunakan /subscribe untuk langganan")
        
        return "\n".join(lines)


# Singleton instance
notification_manager = NotificationManager()
