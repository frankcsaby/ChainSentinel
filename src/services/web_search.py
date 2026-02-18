from duckduckgo_search import DDGS
from loguru import logger
import time

class WebSearchService:
    """
    Internetes kereső szolgáltatás (OSINT) a DuckDuckGo API-n keresztül.
    """

    def search_news(self, keyword: str, max_results: int = 3) -> str:
        """
        Hírek és cikkek keresése a megadott kulcsszóra.
        Visszaadja a találatokat egy formázott stringben.
        """
        query = f"{keyword} crypto scam hack analysis news"
        logger.info(f"Webes keresés indítása: '{query}'...")
        
        results_text = ""
        
        try:
            with DDGS() as ddgs:
                # 3 másodperces timeout, hogy ne akadjon meg a program
                results = list(ddgs.text(query, max_results=max_results))
                
                if not results:
                    logger.warning("Nincs találat a keresésre.")
                    return "No recent news found."

                for i, r in enumerate(results):
                    title = r.get('title', 'No Title')
                    body = r.get('body', 'No Content')
                    link = r.get('href', '#')
                    results_text += f"{i+1}. [{title}] - {body} (Source: {link})\n"
                
                return results_text

        except Exception as e:
            logger.error(f"Hiba a webes keresés során: {e}")
            # Fallback válasz, hogy ne omoljon össze az app
            return "Web search unavailable due to network error."