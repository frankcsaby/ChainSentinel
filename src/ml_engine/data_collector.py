import requests
import pandas as pd
import time
import os
from loguru import logger
from pathlib import Path

# Beállítások
PAGES_TO_FETCH = 4        # Hány oldalt töltsünk le? (1 oldal = 250 coin) -> 4 * 250 = 1000 coin
COINS_PER_PAGE = 250
SLEEP_BETWEEN_PAGES = 10  # Másodperc várakozás, hogy ne tiltsanak ki (429 Rate Limit)
OUTPUT_FILE = "data/dataset/crypto_ml_dataset.csv"

def fetch_market_data():
    logger.info(f"🚀 Adatgyűjtés indítása... Cél: {PAGES_TO_FETCH * COINS_PER_PAGE} token.")
    
    all_coins_data = []
    url = "https://api.coingecko.com/api/v3/coins/markets"
    
    for page in range(1, PAGES_TO_FETCH + 1):
        logger.info(f"➡️ Oldal {page}/{PAGES_TO_FETCH} letöltése...")
        
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': COINS_PER_PAGE,
            'page': page,
            'sparkline': 'false',
            # Kérünk 1h, 24h, 7d és 30d árazási adatokat is a volatilitás vizsgálatához!
            'price_change_percentage': '1h,24h,7d,30d' 
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                all_coins_data.extend(data)
                logger.success(f"✅ {len(data)} token sikeresen letöltve.")
            elif response.status_code == 429:
                logger.error("❌ Rate Limit elérése! Növeld a várakozási időt.")
                break
            else:
                logger.error(f"❌ Ismeretlen hiba: {response.status_code}")
                break
                
        except Exception as e:
            logger.error(f"Hálózati hiba: {e}")
            break
            
        # Várjunk a következő lapozás előtt, hogy kíméljük az API-t
        if page < PAGES_TO_FETCH:
            logger.info(f"⏳ Várakozás {SLEEP_BETWEEN_PAGES} másodpercig az API limit miatt...")
            time.sleep(SLEEP_BETWEEN_PAGES)

    return all_coins_data

def process_and_save_data(raw_data):
    if not raw_data:
        logger.warning("Nincs mit menteni!")
        return

    logger.info("🧮 Adatok tisztítása és Machine Learning feature-ök (jellemzők) generálása...")
    df = pd.DataFrame(raw_data)
    
    # 1. Feature Engineering (Saját matekos oszlopok létrehozása az ML számára)
    
    # Biztonságos osztás (ne legyen nullával osztás)
    df['liquidity_ratio'] = df.apply(
        lambda row: row['total_volume'] / row['market_cap'] if pd.notnull(row['market_cap']) and row['market_cap'] > 0 else 0, 
        axis=1
    )
    
    # Kiszámoljuk a 24 órás áringadozás (High - Low) százalékos mértékét
    df['volatility_24h_pct'] = df.apply(
        lambda row: ((row['high_24h'] - row['low_24h']) / row['current_price'] * 100) 
        if pd.notnull(row['current_price']) and row['current_price'] > 0 else 0, 
        axis=1
    )
    
    # Hány százalékra van az All-Time-High (ATH) csúcstól? (Ha nagyon lent van, gyanús lehet)
    df['ath_drawdown_pct'] = df['ath_change_percentage']

    # 2. Célváltozó (Target Label) szimulálása a betanításhoz
    # A gépi tanulásnál kell egy "Megoldókulcs" (0 = Safe, 1 = Scam/High Risk).
    # Mivel nincs tökéletes adatbázisunk, most egy heurisztikával "felcímkézzük" őket.
    # Szabály: Ha nagyon alacsony a likviditás ÉS nagyon esett az ár = Kockázatos (1)
    def label_risk(row):
        if row['liquidity_ratio'] < 0.02 and row['price_change_percentage_30d_in_currency'] < -50:
            return 1 # Magas kockázat / Dead coin
        elif row['market_cap_rank'] > 800 and row['volatility_24h_pct'] > 30:
            return 1 # Magas kockázat / Pump & Dump gyanú
        else:
            return 0 # Viszonylag biztonságos

    df['TARGET_RISK'] = df.apply(label_risk, axis=1)

    # 3. Csak a releváns oszlopokat tartjuk meg a modell számára
    columns_to_keep = [
        'id', 'symbol', 'name', 'market_cap_rank', 'current_price', 
        'market_cap', 'total_volume', 'liquidity_ratio', 'volatility_24h_pct',
        'price_change_percentage_1h_in_currency', 'price_change_percentage_24h', 
        'price_change_percentage_7d_in_currency', 'price_change_percentage_30d_in_currency',
        'ath_drawdown_pct', 'TARGET_RISK'
    ]
    
    # Hiányzó adatok (NaN) kitöltése 0-val
    ml_df = df[columns_to_keep].fillna(0)
    
    # Mentés CSV-be
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    ml_df.to_csv(OUTPUT_FILE, index=False)
    
    logger.success(f"💾 Adathalmaz elmentve: {OUTPUT_FILE}")
    logger.info(f"📊 Adatok eloszlása a TARGET_RISK oszlopban:\n{ml_df['TARGET_RISK'].value_counts()}")

if __name__ == "__main__":
    raw_api_data = fetch_market_data()
    process_and_save_data(raw_api_data)