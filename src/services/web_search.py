import asyncio
from duckduckgo_search import DDGS
from loguru import logger

class WebSearchService:
    def _search_sync(self, keyword: str, max_results: int) -> str:
        """A szinkron kereső logika (belső használatra)."""
        query = f"{keyword} crypto scam hack analysis news"
        results_text = ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if not results:
                    return "No recent news found."
                for i, r in enumerate(results):
                    results_text += f"{i+1}. [{r.get('title', '')}] - {r.get('body', '')}\n"
                return results_text
        except Exception as e:
            logger.error(f"Hiba a webes keresés során: {e}")
            return "Web search unavailable."

    async def search_news(self, keyword: str, max_results: int = 3) -> str:
        """
        Aszinkron wrapper a szinkron kereséshez. Külön szálon (Thread) futtatja.
        """
        logger.info(f"Keresés háttérszálon: '{keyword}'...")
        return await asyncio.to_thread(self._search_sync, keyword, max_results)