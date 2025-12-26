"""
Configuration settings for AI Financial Advisor
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# API Keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# Data storage paths
DATA_DIR = BASE_DIR / "data"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
ALERTS_FILE = DATA_DIR / "alerts.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Market settings
DEFAULT_MARKET = os.getenv("DEFAULT_MARKET", "IDX")
ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))

# IDX Stock suffixes for Yahoo Finance
IDX_SUFFIX = ".JK"

# Gemini settings
GEMINI_MODEL = "gemini-2.5-flash"

# Common IDX stocks for quick reference
POPULAR_IDX_STOCKS = [
    "BBCA", "BBRI", "BMRI", "BBNI",  # Banking
    "TLKM", "EXCL", "ISAT",           # Telecom
    "ASII", "UNTR",                    # Automotive
    "UNVR", "ICBP", "INDF",           # Consumer
    "GOTO", "BUKA", "EMTK",           # Tech
    "ANTM", "INCO", "PTBA",           # Mining
    "PGAS", "AKRA",                    # Energy
]

# Database configuration
# Format: postgresql://user:password@host:port/database
# For local development: postgresql://postgres:password@localhost:5432/financial_advisor
# Set USE_DATABASE=true to enable PostgreSQL, otherwise JSON files will be used
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"

