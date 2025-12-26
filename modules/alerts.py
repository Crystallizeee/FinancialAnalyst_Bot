"""
Price Alert Module
Manages stock price alerts for users
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import sys
sys.path.append('..')
from config.settings import ALERTS_FILE, USE_DATABASE


class AlertType(Enum):
    ABOVE = "above"
    BELOW = "below"


class AlertManager:
    """Manages stock price alerts with database or JSON fallback"""
    
    def __init__(self):
        self.alerts_file = ALERTS_FILE
        self.use_db = USE_DATABASE
        
        if self.use_db:
            try:
                from modules.database import db_manager, Alert
                self.db = db_manager
                self.Alert = Alert
                if not self.db.is_connected():
                    print("⚠️ Alerts: Database not connected, using JSON")
                    self.use_db = False
            except Exception as e:
                print(f"⚠️ Alerts: Database import failed: {e}")
                self.use_db = False
        
        if not self.use_db:
            self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create alerts file if it doesn't exist"""
        if not self.alerts_file.exists():
            self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load alerts from file"""
        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save alerts to file"""
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        return datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    
    def create_alert(self, user_id: str, stock_code: str, alert_type: str, target_price: float) -> Dict[str, Any]:
        """Create a new price alert"""
        user_id = str(user_id)
        stock_code = stock_code.upper()
        
        if self.use_db:
            session = self.db.get_session()
            try:
                alert = self.Alert(
                    telegram_id=user_id,
                    stock_code=stock_code,
                    condition=alert_type.lower(),
                    target_price=target_price,
                    is_active=True
                )
                session.add(alert)
                session.commit()
                
                return {
                    "id": str(alert.id),
                    "stock": stock_code,
                    "type": alert_type.lower(),
                    "target_price": target_price,
                    "active": True,
                    "created_at": alert.created_at.isoformat() if alert.created_at else datetime.now().isoformat()
                }
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        else:
            # JSON fallback
            data = self._load_data()
            
            if user_id not in data:
                data[user_id] = []
            
            alert = {
                "id": self._generate_alert_id(),
                "stock": stock_code,
                "type": alert_type.lower(),
                "target_price": target_price,
                "active": True,
                "created_at": datetime.now().isoformat(),
                "triggered_at": None
            }
            
            data[user_id].append(alert)
            self._save_data(data)
            
            return alert
    
    def delete_alert(self, user_id: str, alert_id: str) -> bool:
        """Delete an alert"""
        user_id = str(user_id)
        
        if self.use_db:
            session = self.db.get_session()
            try:
                alert = session.query(self.Alert).filter_by(
                    telegram_id=user_id, id=int(alert_id)
                ).first()
                if alert:
                    session.delete(alert)
                    session.commit()
                    return True
                return False
            except Exception:
                session.rollback()
                return False
            finally:
                session.close()
        else:
            data = self._load_data()
            
            if user_id not in data:
                return False
            
            initial_length = len(data[user_id])
            data[user_id] = [a for a in data[user_id] if a["id"] != alert_id]
            
            if len(data[user_id]) < initial_length:
                self._save_data(data)
                return True
            return False
    
    def get_user_alerts(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all alerts for a user"""
        user_id = str(user_id)
        
        if self.use_db:
            session = self.db.get_session()
            try:
                query = session.query(self.Alert).filter_by(telegram_id=user_id)
                if active_only:
                    query = query.filter_by(is_active=True)
                
                return [{
                    "id": str(a.id),
                    "stock": a.stock_code,
                    "type": a.condition,
                    "target_price": a.target_price,
                    "active": a.is_active,
                    "created_at": a.created_at.isoformat() if a.created_at else ""
                } for a in query.all()]
            finally:
                session.close()
        else:
            data = self._load_data()
            alerts = data.get(user_id, [])
            if active_only:
                return [a for a in alerts if a.get("active", False)]
            return alerts
    
    def get_all_active_alerts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all active alerts grouped by user"""
        if self.use_db:
            session = self.db.get_session()
            try:
                alerts = session.query(self.Alert).filter_by(is_active=True).all()
                result = {}
                for a in alerts:
                    if a.telegram_id not in result:
                        result[a.telegram_id] = []
                    result[a.telegram_id].append({
                        "id": str(a.id),
                        "stock": a.stock_code,
                        "type": a.condition,
                        "target_price": a.target_price,
                        "active": True
                    })
                return result
            finally:
                session.close()
        else:
            data = self._load_data()
            result = {}
            for user_id, alerts in data.items():
                active_alerts = [a for a in alerts if a.get("active", False)]
                if active_alerts:
                    result[user_id] = active_alerts
            return result
    
    def trigger_alert(self, user_id: str, alert_id: str) -> Optional[Dict[str, Any]]:
        """Mark an alert as triggered"""
        user_id = str(user_id)
        
        if self.use_db:
            session = self.db.get_session()
            try:
                alert = session.query(self.Alert).filter_by(
                    telegram_id=user_id, id=int(alert_id)
                ).first()
                if alert:
                    alert.is_active = False
                    alert.triggered_at = datetime.utcnow()
                    session.commit()
                    return {
                        "id": str(alert.id),
                        "stock": alert.stock_code,
                        "type": alert.condition,
                        "target_price": alert.target_price
                    }
                return None
            except Exception:
                session.rollback()
                return None
            finally:
                session.close()
        else:
            data = self._load_data()
            
            if user_id not in data:
                return None
            
            for alert in data[user_id]:
                if alert["id"] == alert_id:
                    alert["active"] = False
                    alert["triggered_at"] = datetime.now().isoformat()
                    self._save_data(data)
                    return alert
            
            return None
    
    def check_alert(self, alert: Dict[str, Any], current_price: float) -> bool:
        """Check if an alert should be triggered"""
        if not alert.get("active", False):
            return False
        
        target = alert["target_price"]
        alert_type = alert["type"]
        
        if alert_type == "above" and current_price >= target:
            return True
        elif alert_type == "below" and current_price <= target:
            return True
        
        return False
    
    def format_alerts(self, alerts: List[Dict[str, Any]]) -> str:
        """
        Format alerts into readable summary
        
        Args:
            alerts: List of alerts
            
        Returns:
            Formatted string
        """
        if not alerts:
            return "🔔 Tidak ada alert aktif. Gunakan /alert untuk membuat alert baru."
        
        lines = ["🔔 **PRICE ALERTS**", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        for alert in alerts:
            stock = alert["stock"]
            alert_type = alert["type"].upper()
            target = alert["target_price"]
            created = alert["created_at"][:10]
            alert_id = alert["id"]
            
            emoji = "📈" if alert_type == "ABOVE" else "📉"
            
            lines.append(f"{emoji} **{stock}** {alert_type} Rp {target:,.0f}")
            lines.append(f"   📅 Created: {created}")
            lines.append(f"   🆔 ID: `{alert_id}`")
            lines.append("")
        
        lines.append("_Gunakan /deletealert <id> untuk menghapus alert_")
        
        return "\n".join(lines)
    
    def format_triggered_alert(self, alert: Dict[str, Any], current_price: float) -> str:
        """
        Format triggered alert notification
        
        Args:
            alert: Triggered alert
            current_price: Current stock price
            
        Returns:
            Formatted notification
        """
        stock = alert["stock"]
        alert_type = alert["type"].upper()
        target = alert["target_price"]
        
        emoji = "🚨" if alert_type == "ABOVE" else "⚠️"
        direction = "naik di atas" if alert_type == "ABOVE" else "turun di bawah"
        
        return f"""
{emoji} **PRICE ALERT TRIGGERED!**
━━━━━━━━━━━━━━━━━━━━━━

📊 **{stock}** telah {direction} target!

🎯 Target: Rp {target:,.0f}
💰 Harga saat ini: Rp {current_price:,.0f}

_Alert ini sudah dinonaktifkan._
"""


# Singleton instance
alert_manager = AlertManager()
