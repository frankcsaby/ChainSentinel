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
        Ez hozza le a pillanatnyi adatokat, leírásokat és közösségi statisztikákat.
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

    async def get_historical_prices(self, coin_id: str, days: int = 30) -> list:
        """
        Letölti az elmúlt X nap történelmi árfolyamadatait (Time-Series).
        Ez felelős azért, hogy a PDF generátor meg tudja rajzolni a trendvonalat.
        """
        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd", 
            "days": str(days), 
            "interval": "daily"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"Történelmi adatok lekérése ({days} nap): {coin_id}")
                async with session.get(url, params=params, timeout=settings.API_TIMEOUT) as response:
                    if response.status == 200:
                        data = await response.json()
                        # A CoinGecko [timestamp, price] listák listáját adja vissza
                        # Nekünk csak a price (ár) kell, ami az index 1-en van.
                        prices = [item[1] for item in data.get('prices', [])]
                        return prices
                    
                    elif response.status == 429:
                        logger.warning("Rate limit a történelmi adatoknál!")
                        # Mivel ez általában másodlagos adat, nem csinálunk végtelen retry-t,
                        # csak várunk picit és üres listával térünk vissza, ha nem megy.
                        await asyncio.sleep(5)
                        return []
                    else:
                        logger.error(f"Történelmi adat API hiba: {response.status}")
                        return []
                        
            except Exception as e:
                logger.error(f"Hiba a történelmi adatok letöltésekor: {e}")
                return []