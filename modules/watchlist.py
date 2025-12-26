"""
Watchlist Module
Manages user watchlists for tracking stocks
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import DATA_DIR


WATCHLIST_FILE = DATA_DIR / "watchlists.json"


class WatchlistManager:
    """Manages user stock watchlists"""
    
    def __init__(self):
        self.watchlist_file = WATCHLIST_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create watchlist file if it doesn't exist"""
        if not self.watchlist_file.exists():
            self.watchlist_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load watchlists from file"""
        try:
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save watchlists to file"""
        with open(self.watchlist_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def add_stock(self, user_id: str, stock_code: str) -> bool:
        """
        Add a stock to user's watchlist
        
        Args:
            user_id: Telegram user ID
            stock_code: Stock ticker
            
        Returns:
            True if added, False if already exists
        """
        data = self._load_data()
        user_id = str(user_id)
        stock_code = stock_code.upper()
        
        if user_id not in data:
            data[user_id] = {
                "stocks": [],
                "created_at": datetime.now().isoformat()
            }
        
        if stock_code in data[user_id]["stocks"]:
            return False
        
        data[user_id]["stocks"].append(stock_code)
        self._save_data(data)
        return True
    
    def remove_stock(self, user_id: str, stock_code: str) -> bool:
        """
        Remove a stock from user's watchlist
        
        Args:
            user_id: Telegram user ID
            stock_code: Stock ticker
            
        Returns:
            True if removed, False if not found
        """
        data = self._load_data()
        user_id = str(user_id)
        stock_code = stock_code.upper()
        
        if user_id not in data or stock_code not in data[user_id]["stocks"]:
            return False
        
        data[user_id]["stocks"].remove(stock_code)
        self._save_data(data)
        return True
    
    def get_watchlist(self, user_id: str) -> List[str]:
        """
        Get user's watchlist
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of stock codes
        """
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            return []
        
        return data[user_id].get("stocks", [])
    
    def clear_watchlist(self, user_id: str) -> bool:
        """
        Clear user's entire watchlist
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if cleared
        """
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id in data:
            data[user_id]["stocks"] = []
            self._save_data(data)
        
        return True


# Singleton instance
watchlist_manager = WatchlistManager()
