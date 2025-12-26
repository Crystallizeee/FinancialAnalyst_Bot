# 🤖 AI Financial Advisor Bot

Telegram Bot AI untuk analisis saham Indonesia (IDX) dengan Google Gemini AI, powered by Yahoo Finance dan PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-green.svg)

## ✨ Features

### 📊 Analysis & Research
- **AI Stock Analysis** - Analisis lengkap dengan Gemini AI
- **Technical Analysis** - RSI, MACD, SMA, Bollinger Bands
- **News & Sentiment** - Berita terkini dari Serper.dev
- **Stock Screener** - Filter berdasarkan P/E, dividend, dll
- **Stock Comparison** - Bandingkan 2 saham

### � Market Data
- **IHSG Index** - Data real-time indeks
- **Currency Rates** - Kurs USD, EUR, SGD, dll
- **Sector Performance** - Kinerja per sektor
- **Charts** - Candlestick & comparison charts

### 💼 Portfolio Management
- **Portfolio Tracking** - Catat buy/sell
- **Diversification Analysis** - Skor diversifikasi 0-100
- **Export Reports** - PDF & Excel
- **Transaction History** - Riwayat lengkap

### 🔔 Alerts & Notifications
- **Price Alerts** - Notifikasi harga target
- **Daily Summary** - Ringkasan harian jam 17:00 WIB
- **Watchlist** - Pantau saham favorit

### 🤖 AI Pro
- **Risk Profiling** - Conservative/Moderate/Aggressive
- **Personalized Advice** - Saran sesuai profil
- **Market Prediction** - Prediksi tren AI
- **Conversation Memory** - AI ingat preferensi

### 🗃️ Database
- **PostgreSQL** - Production database
- **JSON Fallback** - Development mode

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Crystallizeee/FinancialAnalyst_Bot.git
cd FinancialAnalyst_Bot
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
copy .env.example .env
# Edit .env dengan API keys kamu
```

**Required API Keys:**
| API | Source |
|-----|--------|
| Telegram Bot Token | [@BotFather](https://t.me/botfather) |
| Gemini API Key | [Google AI Studio](https://aistudio.google.com/apikey) |
| Serper API Key | [serper.dev](https://serper.dev) |

### 3. Database (Optional)

For PostgreSQL:
```env
USE_DATABASE=true
DATABASE_URL=postgresql://user:pass@host:5432/database
```

Default: JSON files (no setup needed)

### 4. Run Bot

```bash
python main.py
```

## 📱 Commands

### Analysis
| Command | Description |
|---------|-------------|
| `/analyze <code>` | AI analysis |
| `/recommend <code>` | Buy/Sell recommendation |
| `/ta <code>` | Technical analysis |
| `/news <code>` | Latest news |
| `/compare <A> <B>` | Compare stocks |
| `/screener <filter>` | Stock screener |

### Market
| Command | Description |
|---------|-------------|
| `/ihsg` | IHSG index data |
| `/kurs` | Currency rates |
| `/sector` | Sector performance |
| `/chart <code>` | Price chart |

### Portfolio
| Command | Description |
|---------|-------------|
| `/portfolio` | View portfolio |
| `/buy <code> <qty> <price>` | Record buy |
| `/sell <code> <qty> <price>` | Record sell |
| `/history` | Transaction history |
| `/diversify` | Diversification analysis |
| `/export <pdf/excel>` | Export report |

### Alerts
| Command | Description |
|---------|-------------|
| `/alert <code> above/below <price>` | Set alert |
| `/alerts` | View alerts |
| `/subscribe` | Daily notifications |
| `/watchlist` | Manage watchlist |

### AI Pro
| Command | Description |
|---------|-------------|
| `/profile` | Set risk profile |
| `/advice` | Personalized advice |
| `/predict <code>` | AI prediction |
| `/ask <question>` | Ask AI |

## 📁 Project Structure

```
FinancialAnalyst_Bot/
├── config/
│   └── settings.py           # Configuration
├── modules/
│   ├── stock_data.py         # Yahoo Finance
│   ├── gemini_ai.py          # Gemini AI
│   ├── serper_search.py      # News search
│   ├── portfolio.py          # Portfolio (DB/JSON)
│   ├── alerts.py             # Price alerts (DB/JSON)
│   ├── market_data.py        # IHSG & Currency
│   ├── chart_generator.py    # Chart creation
│   ├── notifications.py      # Subscriptions
│   ├── portfolio_analysis.py # Diversification & Export
│   ├── user_profile.py       # Risk profiling
│   └── database.py           # SQLAlchemy models
├── handlers/
│   └── telegram_handlers.py  # Bot commands
├── data/                     # JSON storage
├── main.py                   # Entry point
├── requirements.txt
└── .env.example
```

## 🛠️ Tech Stack

- **Python 3.11+**
- **python-telegram-bot** - Telegram API
- **google-genai** - Gemini AI
- **yfinance** - Stock data
- **SQLAlchemy** - Database ORM
- **psycopg2** - PostgreSQL driver
- **matplotlib/mplfinance** - Charts
- **reportlab/openpyxl** - PDF/Excel export
- **APScheduler** - Background jobs

## ⚠️ Disclaimer

**Ini bukan nasihat finansial profesional.** Bot ini dibuat untuk tujuan edukasi. Selalu lakukan riset sendiri sebelum mengambil keputusan investasi.

