"""
Database Repository Module
Provides repository pattern for database operations with fallback to JSON
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import USE_DATABASE, DATA_DIR


class BaseRepository:
    """Base repository with JSON fallback support"""
    
    def __init__(self, json_file: Path = None):
        self.json_file = json_file
        self.use_db = USE_DATABASE
        
        if self.use_db:
            try:
                from modules.database import db_manager
                self.db = db_manager
                if not self.db.is_connected():
                    print("⚠️ Database not connected, falling back to JSON")
                    self.use_db = False
            except Exception as e:
                print(f"⚠️ Database import failed: {e}, using JSON")
                self.use_db = False
        
        if not self.use_db and self.json_file:
            self._ensure_json_exists()
    
    def _ensure_json_exists(self):
        """Create JSON file if it doesn't exist"""
        if self.json_file and not self.json_file.exists():
            self.json_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_json({})
    
    def _load_json(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_json(self, data: Dict[str, Any]):
        """Save data to JSON file"""
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


class PortfolioRepository(BaseRepository):
    """Repository for portfolio operations"""
    
    def __init__(self):
        super().__init__(DATA_DIR / "portfolios.json")
    
    def get_holdings(self, telegram_id: str) -> Dict[str, Any]:
        """Get user's holdings"""
        telegram_id = str(telegram_id)
        
        if self.use_db:
            from modules.database import Portfolio, get_db
            session = get_db()
            try:
                holdings = {}
                records = session.query(Portfolio).filter_by(telegram_id=telegram_id).all()
                for rec in records:
                    holdings[rec.stock_code] = {
                        "quantity": rec.quantity,
                        "avg_price": rec.avg_price,
                        "total_invested": rec.total_invested
                    }
                return holdings
            finally:
                session.close()
        else:
            data = self._load_json()
            if telegram_id in data:
                return data[telegram_id].get("holdings", {})
            return {}
    
    def add_buy(self, telegram_id: str, stock_code: str, quantity: int, price: float) -> Dict[str, Any]:
        """Add a buy transaction"""
        telegram_id = str(telegram_id)
        stock_code = stock_code.upper()
        
        if self.use_db:
            from modules.database import Portfolio, Transaction, get_db
            session = get_db()
            try:
                # Update or create holding
                holding = session.query(Portfolio).filter_by(
                    telegram_id=telegram_id, stock_code=stock_code
                ).first()
                
                if holding:
                    old_total = holding.quantity * holding.avg_price
                    new_total = old_total + (quantity * price)
                    new_quantity = holding.quantity + quantity
                    holding.quantity = new_quantity
                    holding.avg_price = new_total / new_quantity if new_quantity > 0 else 0
                    holding.total_invested = new_total
                else:
                    holding = Portfolio(
                        telegram_id=telegram_id,
                        stock_code=stock_code,
                        quantity=quantity,
                        avg_price=price,
                        total_invested=quantity * price
                    )
                    session.add(holding)
                
                # Add transaction
                tx = Transaction(
                    telegram_id=telegram_id,
                    transaction_type="BUY",
                    stock_code=stock_code,
                    quantity=quantity,
                    price=price,
                    total=quantity * price
                )
                session.add(tx)
                session.commit()
                
                return {
                    "stock": stock_code,
                    "quantity": holding.quantity,
                    "avg_price": holding.avg_price,
                    "total_invested": holding.total_invested
                }
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        else:
            # JSON fallback - same logic as original PortfolioManager
            data = self._load_json()
            
            if telegram_id not in data:
                data[telegram_id] = {"holdings": {}, "transactions": [], "created_at": datetime.now().isoformat()}
            
            portfolio = data[telegram_id]
            
            if stock_code not in portfolio["holdings"]:
                portfolio["holdings"][stock_code] = {"quantity": 0, "avg_price": 0, "total_invested": 0}
            
            holding = portfolio["holdings"][stock_code]
            old_total = holding["quantity"] * holding["avg_price"]
            new_total = old_total + (quantity * price)
            new_quantity = holding["quantity"] + quantity
            
            holding["quantity"] = new_quantity
            holding["avg_price"] = new_total / new_quantity if new_quantity > 0 else 0
            holding["total_invested"] = new_total
            
            transaction = {
                "type": "BUY",
                "stock": stock_code,
                "quantity": quantity,
                "price": price,
                "total": quantity * price,
                "timestamp": datetime.now().isoformat()
            }
            portfolio["transactions"].append(transaction)
            
            self._save_json(data)
            
            return {
                "stock": stock_code,
                "quantity": holding["quantity"],
                "avg_price": holding["avg_price"],
                "total_invested": holding["total_invested"],
                "transaction": transaction
            }
    
    def add_sell(self, telegram_id: str, stock_code: str, quantity: int, price: float) -> Optional[Dict[str, Any]]:
        """Add a sell transaction"""
        telegram_id = str(telegram_id)
        stock_code = stock_code.upper()
        
        if self.use_db:
            from modules.database import Portfolio, Transaction, get_db
            session = get_db()
            try:
                holding = session.query(Portfolio).filter_by(
                    telegram_id=telegram_id, stock_code=stock_code
                ).first()
                
                if not holding or holding.quantity < quantity:
                    return None
                
                avg_buy_price = holding.avg_price
                profit_per_share = price - avg_buy_price
                total_profit = profit_per_share * quantity
                profit_pct = (profit_per_share / avg_buy_price * 100) if avg_buy_price else 0
                
                new_quantity = holding.quantity - quantity
                if new_quantity == 0:
                    session.delete(holding)
                else:
                    holding.quantity = new_quantity
                    holding.total_invested = new_quantity * holding.avg_price
                
                tx = Transaction(
                    telegram_id=telegram_id,
                    transaction_type="SELL",
                    stock_code=stock_code,
                    quantity=quantity,
                    price=price,
                    total=quantity * price,
                    profit=total_profit,
                    profit_pct=profit_pct
                )
                session.add(tx)
                session.commit()
                
                return {
                    "stock": stock_code,
                    "sold_quantity": quantity,
                    "sell_price": price,
                    "profit": total_profit,
                    "profit_pct": profit_pct,
                    "remaining_quantity": new_quantity
                }
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        else:
            # JSON fallback
            data = self._load_json()
            
            if telegram_id not in data or stock_code not in data[telegram_id].get("holdings", {}):
                return None
            
            portfolio = data[telegram_id]
            holding = portfolio["holdings"][stock_code]
            
            if holding["quantity"] < quantity:
                return None
            
            avg_buy_price = holding["avg_price"]
            profit_per_share = price - avg_buy_price
            total_profit = profit_per_share * quantity
            profit_pct = (profit_per_share / avg_buy_price * 100) if avg_buy_price else 0
            
            new_quantity = holding["quantity"] - quantity
            if new_quantity == 0:
                del portfolio["holdings"][stock_code]
            else:
                holding["quantity"] = new_quantity
                holding["total_invested"] = new_quantity * holding["avg_price"]
            
            transaction = {
                "type": "SELL",
                "stock": stock_code,
                "quantity": quantity,
                "price": price,
                "total": quantity * price,
                "profit": total_profit,
                "profit_pct": profit_pct,
                "timestamp": datetime.now().isoformat()
            }
            portfolio["transactions"].append(transaction)
            
            self._save_json(data)
            
            return {
                "stock": stock_code,
                "sold_quantity": quantity,
                "sell_price": price,
                "profit": total_profit,
                "profit_pct": profit_pct,
                "remaining_quantity": new_quantity,
                "transaction": transaction
            }
    
    def get_transactions(self, telegram_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's transaction history"""
        telegram_id = str(telegram_id)
        
        if self.use_db:
            from modules.database import Transaction, get_db
            session = get_db()
            try:
                records = session.query(Transaction).filter_by(
                    telegram_id=telegram_id
                ).order_by(Transaction.timestamp.desc()).limit(limit).all()
                
                return [{
                    "type": rec.transaction_type,
                    "stock": rec.stock_code,
                    "quantity": rec.quantity,
                    "price": rec.price,
                    "total": rec.total,
                    "profit": rec.profit,
                    "profit_pct": rec.profit_pct,
                    "timestamp": rec.timestamp.isoformat() if rec.timestamp else ""
                } for rec in records]
            finally:
                session.close()
        else:
            data = self._load_json()
            if telegram_id in data:
                transactions = data[telegram_id].get("transactions", [])
                return transactions[-limit:][::-1]
            return []


# Singleton instance
portfolio_repo = PortfolioRepository()
