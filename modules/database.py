"""
Database Module
SQLAlchemy models and database connection for PostgreSQL
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import sys
sys.path.append('..')
from config.settings import DATABASE_URL, USE_DATABASE

Base = declarative_base()


# ============== MODELS ==============

class User(Base):
    """User profile and settings"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    chat_id = Column(String(50))
    risk_profile = Column(String(20))  # conservative, moderate, aggressive
    investment_goals = Column(JSON, default=list)
    preferred_sectors = Column(JSON, default=list)
    conversation_history = Column(JSON, default=list)
    daily_summary_enabled = Column(Boolean, default=False)
    breaking_news_enabled = Column(Boolean, default=False)
    earnings_alerts_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)


class Portfolio(Base):
    """User's stock holdings"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False)
    quantity = Column(Integer, default=0)
    avg_price = Column(Float, default=0)
    total_invested = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    """Buy/Sell transaction history"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), nullable=False, index=True)
    transaction_type = Column(String(10))  # BUY, SELL
    stock_code = Column(String(20), nullable=False)
    quantity = Column(Integer)
    price = Column(Float)
    total = Column(Float)
    profit = Column(Float, nullable=True)
    profit_pct = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Price alerts"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False)
    condition = Column(String(10))  # above, below
    target_price = Column(Float)
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Watchlist(Base):
    """User's watchlist"""
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)


# ============== DATABASE CONNECTION ==============

class DatabaseManager:
    """Manages database connection and sessions"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.engine = None
        self.Session = None
        self._initialized = True
        
        if USE_DATABASE and DATABASE_URL:
            self.connect()
    
    def connect(self):
        """Connect to the database and create tables"""
        try:
            self.engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            print("✅ Database connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.engine = None
            self.Session = None
            return False
    
    def get_session(self):
        """Get a database session"""
        if self.Session:
            return self.Session()
        return None
    
    def close_session(self, session):
        """Close a database session"""
        if session:
            session.close()
    
    def is_connected(self):
        """Check if database is connected"""
        return self.engine is not None and self.Session is not None


# Singleton instance
db_manager = DatabaseManager()


def get_db():
    """Helper to get database session (for dependency injection)"""
    return db_manager.get_session()
