"""
Portfolio Management Module
Tracks user stock portfolios with buy/sell transactions
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import PORTFOLIOS_FILE, USE_DATABASE


class PortfolioManager:
    """Manages user stock portfolios with database or JSON fallback"""
    
    def __init__(self):
        self.portfolios_file = PORTFOLIOS_FILE
        self.use_db = USE_DATABASE
        self.db_session = None
        
        if self.use_db:
            try:
                from modules.database import db_manager, Portfolio, Transaction
                self.db = db_manager
                self.Portfolio = Portfolio
                self.Transaction = Transaction
                if not self.db.is_connected():
                    print("⚠️ Portfolio: Database not connected, using JSON")
                    self.use_db = False
            except Exception as e:
                print(f"⚠️ Portfolio: Database import failed: {e}")
                self.use_db = False
        
        if not self.use_db:
            self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create portfolios file if it doesn't exist"""
        if not self.portfolios_file.exists():
            self.portfolios_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load portfolios from file"""
        try:
            with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save portfolios to file"""
        with open(self.portfolios_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _get_user_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get or create user portfolio"""
        data = self._load_data()
        if str(user_id) not in data:
            data[str(user_id)] = {
                "holdings": {},
                "transactions": [],
                "created_at": datetime.now().isoformat()
            }
            self._save_data(data)
        return data[str(user_id)]
    
    def get_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get user's holdings"""
        user_id = str(user_id)
        
        if self.use_db:
            session = self.db.get_session()
            try:
                holdings = {}
                records = session.query(self.Portfolio).filter_by(telegram_id=user_id).all()
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
            portfolio = self._get_user_portfolio(user_id)
            return portfolio.get("holdings", {})
    
    def add_buy(self, user_id: str, stock_code: str, quantity: int, price: float) -> Dict[str, Any]:
        """
        Record a stock purchase
        
        Args:
            user_id: Telegram user ID
            stock_code: Stock ticker
            quantity: Number of shares
            price: Price per share
            
        Returns:
            Updated holding info
        """
        user_id = str(user_id)
        stock_code = stock_code.upper()
        
        if self.use_db:
            session = self.db.get_session()
            try:
                # Find or create holding
                holding = session.query(self.Portfolio).filter_by(
                    telegram_id=user_id, stock_code=stock_code
                ).first()
                
                if holding:
                    old_total = holding.quantity * holding.avg_price
                    new_total = old_total + (quantity * price)
                    new_quantity = holding.quantity + quantity
                    holding.quantity = new_quantity
                    holding.avg_price = new_total / new_quantity if new_quantity > 0 else 0
                    holding.total_invested = new_total
                else:
                    holding = self.Portfolio(
                        telegram_id=user_id,
                        stock_code=stock_code,
                        quantity=quantity,
                        avg_price=price,
                        total_invested=quantity * price
                    )
                    session.add(holding)
                
                # Add transaction
                tx = self.Transaction(
                    telegram_id=user_id,
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
            # JSON fallback
            data = self._load_data()
            
            if user_id not in data:
                data[user_id] = {"holdings": {}, "transactions": [], "created_at": datetime.now().isoformat()}
            
            portfolio = data[user_id]
            
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
            
            self._save_data(data)
            
            return {
                "stock": stock_code,
                "quantity": holding["quantity"],
                "avg_price": holding["avg_price"],
                "total_invested": holding["total_invested"],
                "transaction": transaction
            }
    
    def add_sell(self, user_id: str, stock_code: str, quantity: int, price: float) -> Optional[Dict[str, Any]]:
        """
        Record a stock sale
        """
        user_id = str(user_id)
        stock_code = stock_code.upper()
        
        if self.use_db:
            session = self.db.get_session()
            try:
                holding = session.query(self.Portfolio).filter_by(
                    telegram_id=user_id, stock_code=stock_code
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
                
                tx = self.Transaction(
                    telegram_id=user_id,
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
            data = self._load_data()
            
            if user_id not in data or stock_code not in data[user_id].get("holdings", {}):
                return None
            
            portfolio = data[user_id]
            holding = portfolio["holdings"][stock_code]
            
            if holding["quantity"] < quantity:
                return None
            
            avg_buy_price = holding["avg_price"]
            profit_per_share = price - avg_buy_price
            total_profit = profit_per_share * quantity
            
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
                "profit_pct": (profit_per_share / avg_buy_price * 100) if avg_buy_price else 0,
                "timestamp": datetime.now().isoformat()
            }
            portfolio["transactions"].append(transaction)
            
            self._save_data(data)
            
            return {
                "stock": stock_code,
                "sold_quantity": quantity,
                "sell_price": price,
                "profit": total_profit,
                "profit_pct": transaction["profit_pct"],
                "remaining_quantity": new_quantity,
                "transaction": transaction
            }
    
    def get_transactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions"""
        user_id = str(user_id)
        
        if self.use_db:
            session = self.db.get_session()
            try:
                records = session.query(self.Transaction).filter_by(
                    telegram_id=user_id
                ).order_by(self.Transaction.timestamp.desc()).limit(limit).all()
                
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
            portfolio = self._get_user_portfolio(user_id)
            transactions = portfolio.get("transactions", [])
            return transactions[-limit:][::-1]
    
    def format_portfolio(self, holdings: Dict[str, Any], current_prices: Dict[str, float] = None) -> str:
        """
        Format portfolio into readable summary
        
        Args:
            holdings: User's holdings
            current_prices: Optional current prices for P/L calculation
            
        Returns:
            Formatted string
        """
        if not holdings:
            return "📊 Portfolio kosong. Gunakan /buy untuk menambah saham."
        
        lines = ["💼 **PORTFOLIO KAMU**", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        total_invested = 0
        total_current = 0
        
        for stock, data in holdings.items():
            qty = data["quantity"]
            avg_price = data["avg_price"]
            invested = qty * avg_price
            total_invested += invested
            
            current_price = (current_prices or {}).get(stock, avg_price)
            current_value = qty * current_price
            total_current += current_value
            
            pnl = current_value - invested
            pnl_pct = (pnl / invested * 100) if invested else 0
            
            emoji = "🟢" if pnl >= 0 else "🔴"
            
            lines.append(f"**{stock}**")
            lines.append(f"   📦 {qty:,} lot @ Rp {avg_price:,.0f}")
            lines.append(f"   💰 Value: Rp {current_value:,.0f}")
            lines.append(f"   {emoji} P/L: Rp {pnl:+,.0f} ({pnl_pct:+.2f}%)")
            lines.append("")
        
        # Summary
        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0
        summary_emoji = "🟢" if total_pnl >= 0 else "🔴"
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"💵 Total Invested: Rp {total_invested:,.0f}")
        lines.append(f"💰 Current Value: Rp {total_current:,.0f}")
        lines.append(f"{summary_emoji} Total P/L: Rp {total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)")
        
        return "\n".join(lines)
    
    def format_transactions(self, transactions: List[Dict[str, Any]]) -> str:
        """Format transactions into readable summary"""
        if not transactions:
            return "📋 Belum ada transaksi. Gunakan /buy atau /sell untuk memulai."
        
        lines = ["📋 RIWAYAT TRANSAKSI", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        for i, tx in enumerate(transactions, 1):
            tx_type = tx.get("type", "?")
            emoji = "🟢 BUY" if tx_type == "BUY" else "🔴 SELL"
            stock = tx.get("stock", "?")
            qty = tx.get("quantity", 0)
            price = tx.get("price", 0)
            total = tx.get("total", 0)
            timestamp = tx.get("timestamp", "")[:10]
            
            lines.append(f"{i}. {emoji} {stock}")
            lines.append(f"   {qty:,} lot @ Rp {price:,.0f}")
            lines.append(f"   Total: Rp {total:,.0f}")
            
            if tx_type == "SELL" and "profit" in tx:
                profit = tx.get("profit", 0)
                profit_pct = tx.get("profit_pct", 0)
                profit_emoji = "📈" if profit >= 0 else "📉"
                lines.append(f"   {profit_emoji} P/L: Rp {profit:+,.0f} ({profit_pct:+.2f}%)")
            
            lines.append(f"   📅 {timestamp}")
            lines.append("")
        
        return "\n".join(lines).strip()


# Singleton instance
portfolio_manager = PortfolioManager()
