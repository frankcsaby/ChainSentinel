from duckduckgo_search import DDGS
from loguru import logger
import asyncio

class NewsService:
    def get_latest_news(self, keyword: str, max_results: int = 3) -> str:
        """
        Friss híreket keres a neten a megadott kulcsszóra.
        Visszaadja a címeket és a rövid leírást egy stringben.
        """
        logger.info(f"Hírek keresése: {keyword}...")
        news_summary = ""
        
        try:
            # Szinkron hívás, de gyors, ezért nem akasztja meg nagyon a programot
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{keyword} crypto news hack scam analysis", max_results=max_results))
                
                if not results:
                    return "No recent news found."

                for i, r in enumerate(results):
                    news_summary += f"{i+1}. {r['title']}: {r['body']}\n"
                
                return news_summary
        except Exception as e:
            logger.error(f"Hiba a hírek keresésekor: {e}")
            return "Error fetching news."