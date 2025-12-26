"""
Serper.dev Search Module
Fetches news and search results about stocks using Serper.dev API
"""
import aiohttp
from typing import Dict, Any, List, Optional
import sys
sys.path.append('..')
from config.settings import SERPER_API_KEY


class SerperSearch:
    """Serper.dev integration for news and market research"""
    
    def __init__(self):
        self.api_key = SERPER_API_KEY
        self.base_url = "https://google.serper.dev"
    
    async def search_news(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for news articles
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of news articles
        """
        url = f"{self.base_url}/news"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "gl": "id",  # Indonesia
            "hl": "id",  # Indonesian language
            "num": num_results
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("news", [])
                    else:
                        print(f"Serper API error: {response.status}")
                        return []
        except Exception as e:
            print(f"Error searching news: {e}")
            return []
    
    async def search_stock_news(self, stock_code: str, company_name: str = "") -> List[Dict[str, Any]]:
        """
        Search for news about a specific stock
        
        Args:
            stock_code: Stock ticker (e.g., 'BBCA')
            company_name: Full company name for better results
            
        Returns:
            List of news articles
        """
        # Build search query
        query_parts = [stock_code, "saham"]
        if company_name:
            query_parts.append(company_name)
        query = " ".join(query_parts)
        
        return await self.search_news(query)
    
    async def search_market_news(self) -> List[Dict[str, Any]]:
        """
        Get general Indonesian stock market news
        
        Returns:
            List of market news articles
        """
        return await self.search_news("IHSG saham Indonesia berita terbaru", num_results=15)
    
    async def web_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        General web search
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            List of search results
        """
        url = f"{self.base_url}/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "gl": "id",
            "hl": "id",
            "num": num_results
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("organic", [])
                    else:
                        return []
        except Exception as e:
            print(f"Error in web search: {e}")
            return []
    
    def format_news_summary(self, news_items: List[Dict[str, Any]], max_items: int = 5) -> str:
        """
        Format news items into readable summary
        
        Args:
            news_items: List of news articles
            max_items: Maximum items to include
            
        Returns:
            Formatted string
        """
        if not news_items:
            return "📰 Tidak ada berita terbaru ditemukan."
        
        lines = ["📰 **BERITA TERKINI**", "━━━━━━━━━━━━━━━━━━━━━━", ""]
        
        for i, item in enumerate(news_items[:max_items], 1):
            title = item.get("title", "No title")
            source = item.get("source", "Unknown")
            date = item.get("date", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")[:150]
            
            lines.append(f"**{i}. {title}**")
            lines.append(f"   📅 {date} | 📰 {source}")
            if snippet:
                lines.append(f"   _{snippet}..._")
            lines.append("")
        
        return "\n".join(lines)
    
    def extract_headlines(self, news_items: List[Dict[str, Any]]) -> List[str]:
        """
        Extract just headlines from news items
        
        Args:
            news_items: List of news articles
            
        Returns:
            List of headlines
        """
        return [item.get("title", "") for item in news_items if item.get("title")]


# Singleton instance
serper_search = SerperSearch()
