import requests
from typing import Dict, Any, List, Optional
import json


class WebSearchTools:
    """Инструменты для поиска актуальной информации в интернете"""
    
    def __init__(self, search_api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        self.search_api_key = search_api_key
        self.search_engine_id = search_engine_id
    
    def google_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Поиск через Google Custom Search API"""
        if not self.search_api_key or not self.search_engine_id:
            return {
                "success": False,
                "error": "Google Search API credentials not configured",
                "results": []
            }
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.search_api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num_results, 10)  # Google API limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayLink": item.get("displayLink", "")
                })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": data.get("searchInformation", {}).get("totalResults", "0"),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Google search error: {str(e)}",
                "results": []
            }
    
    def duckduckgo_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Поиск через DuckDuckGo (простая реализация)"""
        try:
            # This is a simplified implementation
            # In production, you'd want to use a proper DuckDuckGo API or scraping library
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            # Add instant answer if available
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("AbstractSource", "DuckDuckGo"),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", ""),
                    "type": "instant_answer"
                })
            
            # Add related topics
            for topic in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else "Related Topic",
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "type": "related_topic"
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results[:num_results],
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"DuckDuckGo search error: {str(e)}",
                "results": []
            }
    
    def fetch_url_content(self, url: str, max_length: int = 5000) -> Dict[str, Any]:
        """Получить контент по URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            content = response.text
            if len(content) > max_length:
                content = content[:max_length] + "... (truncated)"
            
            return {
                "success": True,
                "url": url,
                "content": content,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching URL content: {str(e)}",
                "url": url,
                "content": None
            }
    
    def search_news(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Поиск новостей (упрощенная реализация)"""
        try:
            # This would typically use a news API like NewsAPI
            # For now, we'll use a general search with news-focused query
            news_query = f"{query} news recent"
            return self.duckduckgo_search(news_query, num_results)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"News search error: {str(e)}",
                "results": []
            }
    
    def search_with_fallback(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Поиск с резервными вариантами"""
        # Try Google first if configured
        if self.search_api_key and self.search_engine_id:
            result = self.google_search(query, num_results)
            if result["success"]:
                return result
        
        # Fallback to DuckDuckGo
        return self.duckduckgo_search(query, num_results)
    
    @staticmethod
    def extract_text_from_html(html_content: str) -> str:
        """Извлечь текст из HTML (упрощенная реализация)"""
        try:
            # This is a very basic HTML text extraction
            # In production, you'd want to use BeautifulSoup or similar
            import re
            
            # Remove script and style elements
            html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            return f"Error extracting text: {str(e)}"