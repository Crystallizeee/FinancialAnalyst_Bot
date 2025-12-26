# 🤖 AI Financial Advisor

Bot Telegram AI untuk analisis saham Indonesia (IDX) menggunakan Google Gemini, Serper.dev, dan Yahoo Finance.

## ✨ Features

- 📊 **Stock Analysis** - Analisis lengkap saham IDX dengan AI
- 💡 **Buy/Sell Recommendations** - Rekomendasi trading berdasarkan data
- 📰 **News & Sentiment** - Berita terkini dan analisis sentimen
- 💼 **Portfolio Tracking** - Catat dan track portfolio kamu
- 🔔 **Price Alerts** - Notifikasi ketika harga mencapai target

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "d:\src_code\Py\Manajement Investasi"
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
# Copy template
copy .env.example .env

# Edit .env dan isi API keys
notepad .env
```

**API Keys yang diperlukan:**
- **Telegram Bot Token**: Dari [@BotFather](https://t.me/botfather)
- **Gemini API Key**: Dari [Google AI Studio](https://aistudio.google.com/apikey)
- **Serper API Key**: Dari [serper.dev](https://serper.dev)

### 3. Run Bot

```bash
python main.py
```

## 📱 Telegram Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome & help | `/start` |
| `/analyze <code>` | Analisis saham | `/analyze BBCA` |
| `/recommend <code>` | Rekomendasi beli/jual | `/recommend TLKM` |
| `/news <code>` | Berita & sentiment | `/news BBRI` |
| `/ask <question>` | Tanya AI | `/ask apa itu P/E ratio?` |
| `/portfolio` | Lihat portfolio | `/portfolio` |
| `/buy <code> <qty> <price>` | Catat beli | `/buy BBCA 100 9500` |
| `/sell <code> <qty> <price>` | Catat jual | `/sell BBCA 50 10000` |
| `/alert <code> <above/below> <price>` | Set alert | `/alert BBCA above 10000` |
| `/alerts` | Lihat alerts | `/alerts` |
| `/deletealert <id>` | Hapus alert | `/deletealert 20231225...` |
| `/market` | Update pasar | `/market` |

## 📁 Project Structure

```
Manajement Investasi/
├── config/
│   └── settings.py          # Configuration
├── modules/
│   ├── stock_data.py         # Yahoo Finance integration
│   ├── gemini_ai.py          # Gemini AI analysis
│   ├── serper_search.py      # News search
│   ├── portfolio.py          # Portfolio management
│   └── alerts.py             # Price alerts
├── handlers/
│   └── telegram_handlers.py  # Bot commands
├── data/
│   ├── portfolios.json       # User portfolios
│   └── alerts.json           # Active alerts
├── main.py                   # Entry point
├── requirements.txt          # Dependencies
└── .env                      # API keys (create from .env.example)
```

## ⚠️ Disclaimer

**Ini bukan nasihat finansial profesional.** Bot ini dibuat untuk tujuan edukasi. Selalu lakukan riset sendiri sebelum mengambil keputusan investasi.
