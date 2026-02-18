import aiohttp
import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from config.settings import settings

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    async def get_coin_data(self, coin_id: str, retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Aszinkron lekérdezés újrapróbálkozási mechanizmussal (Retry Logic).
        """
        url = f"{self.BASE_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true",
            "sparkline": "false"
        }

        async with aiohttp.ClientSession() as session:
            for attempt in range(retries):
                try:
                    logger.info(f"API hívás ({attempt+1}/{retries}): {coin_id}")
                    
                    async with session.get(url, params=params, timeout=settings.API_TIMEOUT) as response:
                        if response.status == 200:
                            return await response.json()
                        
                        elif response.status == 429:
                            # HA TÚL GYORSAN HÍVTUK: VÁRUNK ÉS ÚJRA
                            wait_time = (attempt + 1) * 5  # 5mp, 10mp, 15mp
                            logger.warning(f"Rate Limit (429)! Várakozás {wait_time} másodpercig...")
                            await asyncio.sleep(wait_time)
                            continue  # Újrapróbáljuk a ciklust
                        
                        elif response.status == 404:
                            logger.warning(f"Token nem található: {coin_id}")
                            return None
                        else:
                            logger.error(f"API Hiba: {response.status}")
                            return None
                            
                except Exception as e:
                    logger.exception(f"Hálózati hiba: {e}")
                    return None
            
            logger.error(f"Sikertelen lekérdezés {retries} próba után: {coin_id}")
            return None