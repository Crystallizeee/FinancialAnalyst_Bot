"""
Google Gemini AI Integration Module (New SDK)
Provides AI-powered stock analysis and recommendations
"""
import os
from google import genai
from typing import Dict, Any, Optional
import sys
sys.path.append('..')
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

# Set API key as environment variable for google-genai
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY


class GeminiAI:
    """Google Gemini AI integration for financial analysis"""
    
    def __init__(self):
        self.client = genai.Client()
        self.model = GEMINI_MODEL
        
        # System context for financial advisor
        self.system_context = """
Kamu adalah AI Financial Advisor profesional yang ahli dalam analisis saham Indonesia (IDX).
Tugasmu adalah memberikan analisis yang objektif, edukatif, dan mudah dipahami.

ATURAN PENTING:
1. Selalu berikan disclaimer bahwa ini bukan nasihat finansial profesional
2. Gunakan bahasa Indonesia yang mudah dipahami
3. Berikan analisis berdasarkan data yang diberikan
4. Jelaskan istilah-istilah teknis jika perlu
5. Pertimbangkan kondisi pasar Indonesia
6. Berikan rekomendasi yang seimbang (tidak terlalu bullish atau bearish tanpa alasan)
7. Format jawaban dengan emoji dan bullet points untuk mudah dibaca
"""
    
    async def analyze_stock(self, stock_data: Dict[str, Any], news_summary: str = "") -> str:
        """
        Analyze a stock based on its data and news
        
        Args:
            stock_data: Dictionary with stock information
            news_summary: Optional summary of recent news
            
        Returns:
            AI-generated analysis
        """
        prompt = f"""
{self.system_context}

ANALISIS SAHAM: {stock_data.get('symbol', 'Unknown')} - {stock_data.get('name', 'Unknown')}

DATA SAHAM:
- Harga saat ini: Rp {stock_data.get('current_price', 0):,.0f}
- Perubahan: {stock_data.get('price_change_pct', 0):+.2f}%
- P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}
- P/B Ratio: {stock_data.get('pb_ratio', 'N/A')}
- Dividend Yield: {stock_data.get('dividend_yield', 0)*100:.2f}%
- Market Cap: Rp {stock_data.get('market_cap', 0):,.0f}
- 52-Week High: Rp {stock_data.get('week_52_high', 0):,.0f}
- 52-Week Low: Rp {stock_data.get('week_52_low', 0):,.0f}
- Sektor: {stock_data.get('sector', 'N/A')}
- Volume: {stock_data.get('volume', 0):,.0f}

{f"BERITA TERKINI: {news_summary}" if news_summary else ""}

Berikan analisis komprehensif meliputi:
1. 📊 Ringkasan kondisi saham saat ini
2. 📈 Analisis teknikal sederhana (berdasarkan data yang ada)
3. 💰 Analisis valuasi (apakah murah/mahal berdasarkan P/E, P/B)
4. ⚠️ Risiko yang perlu diperhatikan
5. 💡 Kesimpulan dan pertimbangan

DISCLAIMER: Ini bukan saran investasi profesional.
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Maaf, terjadi kesalahan dalam analisis: {str(e)}"
    
    async def get_recommendation(self, stock_data: Dict[str, Any], user_profile: str = "moderate") -> str:
        """
        Get buy/sell/hold recommendation
        
        Args:
            stock_data: Stock information
            user_profile: Investment profile (conservative, moderate, aggressive)
            
        Returns:
            AI-generated recommendation
        """
        prompt = f"""
{self.system_context}

REKOMENDASI SAHAM: {stock_data.get('symbol', 'Unknown')}

DATA SAHAM:
- Harga: Rp {stock_data.get('current_price', 0):,.0f}
- P/E: {stock_data.get('pe_ratio', 'N/A')}
- P/B: {stock_data.get('pb_ratio', 'N/A')}
- Dividend Yield: {stock_data.get('dividend_yield', 0)*100:.2f}%
- Dari 52-Week High: {stock_data.get('from_52_high_pct', 0):.1f}%
- Dari 52-Week Low: {stock_data.get('from_52_low_pct', 0):.1f}%

Profil Investor: {user_profile}

Berikan rekomendasi dengan format:
1. 🎯 REKOMENDASI: [BELI / JUAL / HOLD / WAIT]
2. 📊 Confidence Level: [Rendah / Sedang / Tinggi]
3. 💰 Target Harga (jika beli): Rp xxx - Rp xxx
4. 🛑 Stop Loss (jika beli): Rp xxx
5. ⏰ Time Horizon: [Pendek/Menengah/Panjang]
6. 📝 Alasan singkat (3-5 poin)

⚠️ DISCLAIMER: Ini bukan saran investasi. Selalu lakukan riset sendiri.
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Maaf, terjadi kesalahan: {str(e)}"
    
    async def analyze_sentiment(self, news_items: list) -> str:
        """
        Analyze sentiment from news items
        
        Args:
            news_items: List of news headlines and snippets
            
        Returns:
            Sentiment analysis result
        """
        news_text = "\n".join([f"- {item}" for item in news_items[:10]])
        
        prompt = f"""
{self.system_context}

ANALISIS SENTIMEN BERITA:

Berita yang ditemukan:
{news_text}

Berikan analisis sentimen dengan format:
1. 📊 SENTIMEN KESELURUHAN: [POSITIF / NEGATIF / NETRAL]
2. 📈 Skor Sentimen: [1-10] (1 sangat negatif, 10 sangat positif)
3. 🔍 Tema Utama: (3 poin)
4. ⚠️ Potensi Risiko dari Berita
5. 💡 Potensi Peluang dari Berita
6. 📝 Ringkasan (2-3 kalimat)
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Maaf, terjadi kesalahan: {str(e)}"
    
    async def answer_question(self, question: str, context: str = "") -> str:
        """
        Answer general investment questions
        
        Args:
            question: User's question
            context: Optional additional context
            
        Returns:
            AI-generated answer
        """
        prompt = f"""
{self.system_context}

PERTANYAAN USER:
{question}

{f"KONTEKS TAMBAHAN: {context}" if context else ""}

Jawab pertanyaan dengan:
1. Bahasa Indonesia yang mudah dipahami
2. Contoh konkret jika memungkinkan
3. Referensi ke kondisi pasar Indonesia jika relevan
4. Disclaimer jika menyangkut keputusan investasi
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Maaf, terjadi kesalahan: {str(e)}"
    
    async def get_personalized_advice(self, user_context: str, portfolio_data: str, market_data: str) -> str:
        """
        Get personalized investment advice based on user profile
        
        Args:
            user_context: User profile and preferences
            portfolio_data: Current portfolio holdings
            market_data: Current market conditions
        """
        prompt = f"""
{self.system_context}

PERSONALIZED ADVICE REQUEST

=== PROFIL USER ===
{user_context}

=== PORTFOLIO SAAT INI ===
{portfolio_data}

=== KONDISI PASAR ===
{market_data}

Berdasarkan profil risiko dan tujuan investasi user, berikan saran yang SPESIFIK dan ACTIONABLE:

1. 📊 EVALUASI PORTFOLIO
   - Apakah sudah sesuai dengan profil risiko?
   - Apakah perlu rebalancing?

2. 🎯 REKOMENDASI SPESIFIK
   - Saham yang cocok untuk ditambah (sesuai profil)
   - Saham yang perlu dikurangi (jika ada)

3. 💡 ACTION ITEMS (3-5 langkah konkret)
   - Apa yang harus dilakukan minggu ini?

4. ⚠️ PERINGATAN KHUSUS
   - Risiko spesifik untuk profil user

Format dengan emoji dan bullet points. Berikan saran yang konkret, bukan generik.
⚠️ DISCLAIMER: Ini bukan saran investasi profesional.
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Maaf, terjadi kesalahan: {str(e)}"
    
    async def predict_market_trend(self, stock_code: str, stock_data: Dict[str, Any], 
                                   technical_data: str, news_summary: str) -> str:
        """
        Predict market trend using AI analysis
        
        Args:
            stock_code: Stock ticker
            stock_data: Current stock data
            technical_data: Technical analysis indicators
            news_summary: Recent news summary
        """
        prompt = f"""
{self.system_context}

MARKET PREDICTION REQUEST: {stock_code}

=== DATA SAHAM ===
- Harga: Rp {stock_data.get('current_price', 0):,.0f}
- Perubahan Hari Ini: {stock_data.get('price_change_pct', 0):+.2f}%
- Volume: {stock_data.get('volume', 0):,.0f}
- 52-Week High: Rp {stock_data.get('week_52_high', 0):,.0f}
- 52-Week Low: Rp {stock_data.get('week_52_low', 0):,.0f}

=== INDIKATOR TEKNIKAL ===
{technical_data}

=== BERITA TERKINI ===
{news_summary if news_summary else "Tidak ada berita signifikan"}

Berikan PREDIKSI TREN dengan format:

📈 PREDIKSI TREN:
   🎯 Jangka Pendek (1-2 minggu): [BULLISH/BEARISH/SIDEWAYS]
   🎯 Jangka Menengah (1-3 bulan): [BULLISH/BEARISH/SIDEWAYS]

📊 CONFIDENCE LEVEL: [Rendah/Sedang/Tinggi] (jelaskan alasan)

💰 TARGET HARGA:
   • Bullish Target: Rp xxx
   • Bearish Target: Rp xxx
   • Support Kuat: Rp xxx
   • Resistance Kuat: Rp xxx

🔮 KATALIS POTENSIAL:
   • Faktor yang bisa mendorong naik
   • Faktor yang bisa mendorong turun

📝 RINGKASAN (2-3 kalimat)

⚠️ DISCLAIMER: Prediksi berdasarkan data historis dan analisis AI. 
Pasar bisa bergerak tidak terduga. Bukan saran investasi.
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Maaf, terjadi kesalahan: {str(e)}"
    
    async def compare_stocks_ai(self, stock1_data: Dict, stock2_data: Dict, user_profile: str = "") -> str:
        """
        AI-powered stock comparison with personalization
        """
        prompt = f"""
{self.system_context}

PERBANDINGAN SAHAM:

=== SAHAM 1: {stock1_data.get('symbol', 'Unknown')} ===
- Harga: Rp {stock1_data.get('current_price', 0):,.0f}
- P/E: {stock1_data.get('pe_ratio', 'N/A')}
- P/B: {stock1_data.get('pb_ratio', 'N/A')}
- Dividend: {stock1_data.get('dividend_yield', 0)*100:.2f}%
- Sektor: {stock1_data.get('sector', 'N/A')}

=== SAHAM 2: {stock2_data.get('symbol', 'Unknown')} ===
- Harga: Rp {stock2_data.get('current_price', 0):,.0f}
- P/E: {stock2_data.get('pe_ratio', 'N/A')}
- P/B: {stock2_data.get('pb_ratio', 'N/A')}
- Dividend: {stock2_data.get('dividend_yield', 0)*100:.2f}%
- Sektor: {stock2_data.get('sector', 'N/A')}

{f"=== PROFIL USER ===" if user_profile else ""}
{user_profile}

Berikan perbandingan dengan format:
1. 📊 Perbandingan Fundamental (tabel sederhana)
2. 🏆 Pemenang per Kategori (Valuasi, Dividen, Growth potential)
3. 🎯 REKOMENDASI: Mana yang lebih cocok dan kenapa
4. ⚠️ Risiko masing-masing
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Maaf, terjadi kesalahan: {str(e)}"


# Singleton instance
gemini_ai = GeminiAI()

