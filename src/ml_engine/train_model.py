import pandas as pd
import numpy as np
import os
import joblib
from loguru import logger
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

# Útvonalak
DATASET_PATH = "data/dataset/crypto_ml_dataset.csv"
MODEL_DIR = "data/models"
MODEL_PATH = f"{MODEL_DIR}/rf_risk_model.pkl"
SCALER_PATH = f"{MODEL_DIR}/scaler.pkl"

def train_and_evaluate():
    logger.info("🧠 Machine Learning betanítás indítása...")

    # 1. Adatok betöltése
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Nem található az adathalmaz: {DATASET_PATH}")
        return

    df = pd.read_csv(DATASET_PATH)
    logger.info(f"📊 Adatok betöltve. Méret: {df.shape[0]} sor, {df.shape[1]} oszlop.")

    # 2. Bemeneti (X) és Cél (y) változók szétválasztása
    # Eldobjuk a neveket és ID-kat, mert azokból nem tanulhat a gép (csak a számokból)
    drop_columns = ['id', 'symbol', 'name', 'TARGET_RISK']
    X = df.drop(columns=drop_columns)
    y = df['TARGET_RISK']

    # 3. Képző és Tesztelő halmazra bontás (80% tanul, 20% vizsgázik)
    # A stratify=y BIZTOSÍTJA, hogy a teszt halmazba is jusson a ritka 1-es (scam) osztályból!
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    logger.info(f"🔪 Adatok felosztva. Tanuló: {len(X_train)}, Teszt: {len(X_test)}")

    # 4. Adatok normalizálása (Skálázás)
    # Hogy a millió dolláros Market Cap ne nyomja el a 2%-os volatilitást
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. Algoritmus kiválasztása és betanítása
    # A class_weight='balanced' oldja meg a 742 vs 8 problémát a képedről!
    logger.info("🌲 Random Forest algoritmus betanítása...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
    
    # ITT TÖRTÉNIK A TANULÁS
    model.fit(X_train_scaled, y_train)
    logger.success("✅ Modell sikeresen betanítva!")

    # 6. Értékelés (Vizsgáztatás a 20% teszt adaton)
    logger.info("📈 Tesztelés az ismeretlen adatokon...")
    y_pred = model.predict(X_test_scaled)
    
    # 7. Eredmények kiírása
    print("\n" + "="*50)
    print("   CONFUSION MATRIX (Tévesztési Mátrix)   ")
    print("="*50)
    print(confusion_matrix(y_test, y_pred))
    print("\n[Sorok: Valóságos érték | Oszlopok: Modell tippje]")
    print("Bal felső: Valós Safe & Safe-nek tippelt")
    print("Jobb alsó: Valós Scam & Scam-nek tippelt")

    print("\n" + "="*50)
    print("   CLASSIFICATION REPORT (Értékelés)   ")
    print("="*50)
    print(classification_report(y_test, y_pred, target_names=['Safe (0)', 'Risk/Scam (1)']))

    # 8. Modell mentése (.pkl fájlba) a valós idejű használathoz
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    logger.info(f"💾 Modell elmentve ide: {MODEL_PATH}")
    logger.info("Mostantól a Risk Engine használhatja az AI modellt!")

if __name__ == "__main__":
    train_and_evaluate()