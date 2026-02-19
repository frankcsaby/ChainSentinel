import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any
from loguru import logger

class RiskEngine:
    def __init__(self):
        # 1. Betöltjük a betanított Machine Learning modellt és a skálázót
        self.model_path = "data/models/rf_risk_model.pkl"
        self.scaler_path = "data/models/scaler.pkl"
        self.ml_enabled = False
        self.model = None
        self.scaler = None
        
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.ml_enabled = True
                logger.info("🤖 Machine Learning Modell sikeresen csatlakoztatva a Risk Engine-hez!")
            except Exception as e:
                logger.error(f"Hiba az ML modell betöltésekor: {e}")
        else:
            logger.warning("ML modell nem található. Visszatérés a statikus algoritmushoz.")

    def calculate_risk_metrics(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Komplex, többdimenziós kockázatelemzés Machine Learning predikcióval."""
        try:
            # --- 1. Alapadatok és régi dimenziók (A Radar Chart-hoz) ---
            price_change = market_data.get('market_data', {}).get('price_change_percentage_24h', 0) or 0
            mcap_rank = market_data.get('market_cap_rank', 1000) or 1000
            dev_stars = market_data.get('developer_data', {}).get('stars', 0) or 0
            twitter_followers = market_data.get('community_data', {}).get('twitter_followers', 0) or 0
            
            volume = market_data.get('market_data', {}).get('total_volume', {}).get('usd', 0) or 0
            mcap = market_data.get('market_data', {}).get('market_cap', {}).get('usd', 1) or 1
            liquidity_ratio = volume / mcap if mcap > 0 else 0

            # Dimenziók pontozása (0-10) a pókháló ábrához
            volatility_score = max(0, 10 - (abs(price_change) / 2))
            liquidity_score = min(10, (liquidity_ratio * 100))
            market_score = 10 if mcap_rank <= 10 else max(0, 10 - (mcap_rank / 50))
            dev_score = min(10, dev_stars / 500)
            community_score = min(10, twitter_followers / 50000)

            dimensions = {
                "Volatility Safety": round(volatility_score, 1),
                "Liquidity Strength": round(liquidity_score, 1),
                "Market Position": round(market_score, 1),
                "Development": round(dev_score, 1),
                "Community": round(community_score, 1)
            }

            # --- 2. MACHINE LEARNING PREDIKCIÓ ---
            ml_risk_score = 50 # Alapértelmezett érték, ha nincs ML

            if self.ml_enabled:
                # Feature-ök kinyerése pontosan olyan sorrendben, ahogy a modell tanulta!
                high_24h = market_data.get('market_data', {}).get('high_24h', {}).get('usd', 0) or 0
                low_24h = market_data.get('market_data', {}).get('low_24h', {}).get('usd', 0) or 0
                current_price = market_data.get('market_data', {}).get('current_price', {}).get('usd', 0) or 0
                
                volatility_24h_pct = ((high_24h - low_24h) / current_price * 100) if current_price > 0 else 0
                
                features = {
                    'market_cap_rank': mcap_rank,
                    'current_price': current_price,
                    'market_cap': mcap,
                    'total_volume': volume,
                    'liquidity_ratio': liquidity_ratio,
                    'volatility_24h_pct': volatility_24h_pct,
                    'price_change_percentage_1h_in_currency': market_data.get('market_data', {}).get('price_change_percentage_1h_in_currency', {}).get('usd', 0) or 0,
                    'price_change_percentage_24h': price_change,
                    'price_change_percentage_7d_in_currency': market_data.get('market_data', {}).get('price_change_percentage_7d_in_currency', {}).get('usd', 0) or 0,
                    'price_change_percentage_30d_in_currency': market_data.get('market_data', {}).get('price_change_percentage_30d_in_currency', {}).get('usd', 0) or 0,
                    'ath_drawdown_pct': market_data.get('market_data', {}).get('ath_change_percentage', {}).get('usd', 0) or 0
                }
                
                # Konvertálás táblázattá (DataFrame) a skálázónak
                df_features = pd.DataFrame([features])
                
                # Skálázás (Normalizálás)
                X_scaled = self.scaler.transform(df_features)
                
                # Predikció: A predict_proba megmondja a valószínűségeket [Safe %, Scam/Risk %]
                probabilities = self.model.predict_proba(X_scaled)[0]
                scam_probability = probabilities[1] # A 2. elem a Scam/Risk esélye
                
                # Konvertáljuk 0-100-as skálára
                ml_risk_score = int(scam_probability * 100)
            else:
                # Fallback: Régi matek, ha valamiért nem töltődött be a modell
                overall_safety = (volatility_score * 0.3) + (liquidity_score * 0.3) + (market_score * 0.2) + (dev_score * 0.1) + (community_score * 0.1)
                ml_risk_score = int(100 - (overall_safety * 10))

            return {
                "quantitative_score": max(0, min(100, ml_risk_score)),
                "dimensions": dimensions,
                "ml_active": self.ml_enabled
            }

        except Exception as e:
            logger.error(f"Hiba a komplex kockázati számításban: {e}")
            return {"quantitative_score": 50, "dimensions": {}, "ml_active": False}

    def get_quant_finance_metrics(self, historical_prices: list) -> Dict[str, Any]:
        """
        Professzionális intézményi kockázati mutatók számítása (Quant Finance).
        Ezek a metrikák (Sharpe, MDD, Volatilitás) bekerülnek az AI promptba és a PDF-be.
        """
        if not historical_prices or len(historical_prices) < 7:
            return {
                "annualized_volatility_pct": 0,
                "max_drawdown_pct": 0,
                "sharpe_ratio": 0,
                "trend_status": "Insufficient Data"
            }

        try:
            prices = np.array(historical_prices)
            # Napi hozamok (Daily Returns) kiszámítása
            # Pl: ha tegnap 100 volt, ma 110, akkor (110-100)/100 = 0.1 (10%)
            returns = np.diff(prices) / prices[:-1]
            
            # 1. Évesített Volatilitás (Annualized Volatility)
            # A napi szórás felszorozva a kereskedési napok gyökével (kriptóban 365 nap)
            daily_volatility = np.std(returns)
            ann_volatility = daily_volatility * np.sqrt(365) * 100

            # 2. Maximum Drawdown (MDD)
            # A legnagyobb történelmi esés a csúcstól a mélypontig a vizsgált időszakon belül
            roll_max = np.maximum.accumulate(prices)
            drawdowns = (prices - roll_max) / roll_max
            max_drawdown = np.min(drawdowns) * 100

            # 3. Sharpe-ráta (Sharpe Ratio Proxy)
            # Hozam/Kockázat arány. A napi volatilitás nem lehet nulla (osztás nullával hiba elkerülése).
            mean_return = np.mean(returns)
            annualized_return = mean_return * 365
            sharpe_ratio = annualized_return / (daily_volatility * np.sqrt(365)) if daily_volatility > 0 else 0

            # 4. Egyszerű trend meghatározás
            trend_status = "Bullish (Uptrend)" if prices[-1] > prices[0] else "Bearish (Downtrend)"

            return {
                "annualized_volatility_pct": round(ann_volatility, 2),
                "max_drawdown_pct": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "trend_status": trend_status
            }
        except Exception as e:
            logger.error(f"Hiba a Quant mutatók számításakor: {e}")
            return {
                "annualized_volatility_pct": 0, 
                "max_drawdown_pct": 0, 
                "sharpe_ratio": 0, 
                "trend_status": "Error"
            }