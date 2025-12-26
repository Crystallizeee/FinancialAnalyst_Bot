"""
User Profile Module
Manages user preferences, risk profiles, and conversation history
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import DATA_DIR


PROFILES_FILE = DATA_DIR / "user_profiles.json"


class UserProfileManager:
    """Manages user profiles, risk preferences, and conversation memory"""
    
    RISK_PROFILES = {
        "conservative": {
            "name": "Konservatif",
            "emoji": "🛡️",
            "description": "Fokus pada keamanan modal, preferensi dividen tinggi",
            "criteria": {
                "min_dividend_yield": 0.04,
                "max_pe_ratio": 15,
                "prefer_bluechip": True,
                "max_volatility": "low"
            }
        },
        "moderate": {
            "name": "Moderat",
            "emoji": "⚖️",
            "description": "Keseimbangan antara pertumbuhan dan keamanan",
            "criteria": {
                "min_dividend_yield": 0.02,
                "max_pe_ratio": 25,
                "prefer_bluechip": True,
                "max_volatility": "medium"
            }
        },
        "aggressive": {
            "name": "Agresif",
            "emoji": "🚀",
            "description": "Fokus pada pertumbuhan tinggi, toleransi risiko tinggi",
            "criteria": {
                "min_dividend_yield": 0,
                "max_pe_ratio": None,
                "prefer_bluechip": False,
                "max_volatility": "high"
            }
        }
    }
    
    def __init__(self):
        self.profiles_file = PROFILES_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create profiles file if it doesn't exist"""
        if not self.profiles_file.exists():
            self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load profiles from file"""
        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save profiles to file"""
        with open(self.profiles_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get or create user profile"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            data[user_id] = {
                "risk_profile": None,
                "investment_goals": [],
                "preferred_sectors": [],
                "conversation_history": [],
                "last_active": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            self._save_data(data)
        
        return data[user_id]
    
    def set_risk_profile(self, user_id: str, risk_level: str) -> bool:
        """
        Set user's risk profile
        
        Args:
            user_id: Telegram user ID
            risk_level: 'conservative', 'moderate', or 'aggressive'
        """
        if risk_level not in self.RISK_PROFILES:
            return False
        
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            self.get_user_profile(user_id)
            data = self._load_data()
        
        data[user_id]["risk_profile"] = risk_level
        data[user_id]["last_active"] = datetime.now().isoformat()
        self._save_data(data)
        return True
    
    def set_investment_goals(self, user_id: str, goals: List[str]) -> bool:
        """Set user's investment goals"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            self.get_user_profile(user_id)
            data = self._load_data()
        
        data[user_id]["investment_goals"] = goals
        data[user_id]["last_active"] = datetime.now().isoformat()
        self._save_data(data)
        return True
    
    def set_preferred_sectors(self, user_id: str, sectors: List[str]) -> bool:
        """Set user's preferred sectors"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            self.get_user_profile(user_id)
            data = self._load_data()
        
        data[user_id]["preferred_sectors"] = sectors
        data[user_id]["last_active"] = datetime.now().isoformat()
        self._save_data(data)
        return True
    
    def add_conversation(self, user_id: str, message: str, response: str):
        """Add conversation to history (keeps last 10)"""
        data = self._load_data()
        user_id = str(user_id)
        
        if user_id not in data:
            self.get_user_profile(user_id)
            data = self._load_data()
        
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_message": message[:500],  # Limit length
            "ai_response": response[:1000]
        }
        
        history = data[user_id].get("conversation_history", [])
        history.append(conversation)
        data[user_id]["conversation_history"] = history[-10:]  # Keep last 10
        data[user_id]["last_active"] = datetime.now().isoformat()
        self._save_data(data)
    
    def get_conversation_context(self, user_id: str) -> str:
        """Get conversation context for AI"""
        profile = self.get_user_profile(str(user_id))
        
        context_parts = []
        
        # Risk profile
        if profile.get("risk_profile"):
            risk = self.RISK_PROFILES.get(profile["risk_profile"], {})
            context_parts.append(f"Profil risiko: {risk.get('name', 'Unknown')} - {risk.get('description', '')}")
        
        # Investment goals
        if profile.get("investment_goals"):
            context_parts.append(f"Tujuan investasi: {', '.join(profile['investment_goals'])}")
        
        # Preferred sectors
        if profile.get("preferred_sectors"):
            context_parts.append(f"Sektor favorit: {', '.join(profile['preferred_sectors'])}")
        
        # Recent conversations
        history = profile.get("conversation_history", [])[-3:]  # Last 3
        if history:
            context_parts.append("Percakapan terakhir:")
            for conv in history:
                context_parts.append(f"- User: {conv['user_message'][:100]}...")
        
        return "\n".join(context_parts) if context_parts else "Belum ada profil"
    
    def format_profile(self, profile: Dict[str, Any]) -> str:
        """Format user profile for display"""
        lines = ["👤 PROFIL KAMU", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        # Risk profile
        risk_level = profile.get("risk_profile")
        if risk_level:
            risk = self.RISK_PROFILES.get(risk_level, {})
            lines.append(f"{risk.get('emoji', '❓')} Profil Risiko: {risk.get('name', 'Unknown')}")
            lines.append(f"   {risk.get('description', '')}")
        else:
            lines.append("❓ Profil Risiko: Belum diatur")
            lines.append("   Gunakan /profile set untuk mengatur")
        lines.append("")
        
        # Investment goals
        goals = profile.get("investment_goals", [])
        if goals:
            lines.append(f"🎯 Tujuan: {', '.join(goals)}")
        else:
            lines.append("🎯 Tujuan: Belum diatur")
        
        # Preferred sectors
        sectors = profile.get("preferred_sectors", [])
        if sectors:
            lines.append(f"🏭 Sektor: {', '.join(sectors)}")
        else:
            lines.append("🏭 Sektor: Belum diatur")
        
        lines.append("")
        lines.append(f"📅 Terakhir Aktif: {profile.get('last_active', '')[:10]}")
        
        return "\n".join(lines)


# Singleton instance
user_profile_manager = UserProfileManager()
