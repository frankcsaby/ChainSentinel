from typing import Dict, Any, List
from loguru import logger

class RiskEngine:
    """
    Kvantitatív kockázatelemző motor.
    A piaci adatok alapján számol kockázati pontszámot (0-100).
    """

    def calculate_risk_metrics(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kiszámolja a technikai kockázati mutatókat.
        """
        try:
            # Adatok kinyerése
            price_change = market_data.get('market_data', {}).get('price_change_percentage_24h', 0)
            market_cap_rank = market_data.get('market_cap_rank', 9999)
            
            # Developer Score (GitHub csillagok alapján)
            dev_stars = market_data.get('developer_data', {}).get('stars', 0)
            
            # Likviditás becslés (Volume / Market Cap)
            volume = market_data.get('market_data', {}).get('total_volume', {}).get('usd', 0)
            mcap = market_data.get('market_data', {}).get('market_cap', {}).get('usd', 1)
            liquidity_ratio = volume / mcap if mcap > 0 else 0

            # --- KOCKÁZATI LOGIKA ---
            risk_score = 50  # Bázis pontszám (Közepes)

            # 1. Volatilitás büntetés
            if abs(price_change) > 10:
                risk_score += 15  # Nagy ingadozás -> Kockázatos
            elif abs(price_change) < 2:
                risk_score -= 5   # Stabil -> Biztonságosabb

            # 2. Rangsor bónusz
            if market_cap_rank and market_cap_rank <= 10:
                risk_score -= 20  # Top 10 coin -> Biztonságos
            elif market_cap_rank > 500:
                risk_score += 20  # Shitcoin kategória -> Kockázatos

            # 3. Fejlesztői aktivitás
            if dev_stars > 1000:
                risk_score -= 10  # Van mögötte munka
            elif dev_stars < 10:
                risk_score += 10  # Nincs fejlesztés (vagy rejtett)

            # 4. Likviditási csapda (Rug pull gyanú)
            if liquidity_ratio < 0.01:
                risk_score += 25  # Nagyon nehéz eladni

            # Normalizálás 0-100 közé
            risk_score = max(0, min(100, risk_score))

            return {
                "quantitative_score": risk_score,
                "metrics": {
                    "liquidity_ratio": round(liquidity_ratio, 4),
                    "volatility_24h": round(price_change, 2),
                    "dev_activity_score": dev_stars
                }
            }

        except Exception as e:
            logger.error(f"Hiba a kockázati számításban: {e}")
            return {"quantitative_score": 50, "metrics": {}}