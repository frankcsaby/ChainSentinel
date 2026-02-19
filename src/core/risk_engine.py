import numpy as np
from typing import Dict, Any
from loguru import logger

class RiskEngine:
    def calculate_risk_metrics(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Komplex, többdimenziós kockázatelemzés."""
        try:
            # 1. Nyers adatok kinyerése
            price_change = market_data.get('market_data', {}).get('price_change_percentage_24h', 0)
            mcap_rank = market_data.get('market_cap_rank', 1000)
            dev_stars = market_data.get('developer_data', {}).get('stars', 0)
            twitter_followers = market_data.get('community_data', {}).get('twitter_followers', 0)
            
            volume = market_data.get('market_data', {}).get('total_volume', {}).get('usd', 0)
            mcap = market_data.get('market_data', {}).get('market_cap', {}).get('usd', 1)
            liquidity_ratio = volume / mcap if mcap > 0 else 0

            # 2. DIMENZIÓK PONtoZÁSA (0 = Veszélyes, 10 = Biztonságos)
            
            # Volatilitás pont (Kisebb ingadozás = több pont)
            volatility_score = max(0, 10 - (abs(price_change) / 2))
            
            # Likviditás pont (Magasabb arány = több pont)
            liquidity_score = min(10, (liquidity_ratio * 100))
            
            # Piaci Erő (Kisebb rank = több pont)
            market_score = 10 if mcap_rank <= 10 else max(0, 10 - (mcap_rank / 50))
            
            # Fejlesztői Aktivitás (Több csillag = több pont)
            dev_score = min(10, dev_stars / 500)
            
            # Közösségi Erő (Több követő = több pont)
            community_score = min(10, twitter_followers / 50000)

            # 3. Aggregáció (Súlyozott átlag)
            overall_safety = (volatility_score * 0.3) + (liquidity_score * 0.3) + (market_score * 0.2) + (dev_score * 0.1) + (community_score * 0.1)
            # Konvertáljuk Kockázati Pontszámmá (100 - Biztonság)
            risk_score = 100 - (overall_safety * 10)

            return {
                "quantitative_score": round(max(0, min(100, risk_score))),
                "dimensions": {
                    "Volatility Safety": round(volatility_score, 1),
                    "Liquidity Strength": round(liquidity_score, 1),
                    "Market Position": round(market_score, 1),
                    "Development": round(dev_score, 1),
                    "Community": round(community_score, 1)
                }
            }
        except Exception as e:
            logger.error(f"Hiba a komplex kockázati számításban: {e}")
            return {"quantitative_score": 50, "dimensions": {}}