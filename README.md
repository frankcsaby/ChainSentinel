# ChainSentinel Enterprise 🛡️

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-green)
![License](https://img.shields.io/badge/license-MIT-orange)

**Advanced AI-Powered Cryptocurrency Risk Analysis & Audit System**

ChainSentinel is a local, privacy-focused tool that leverages Large Language Models (LLM) via Ollama (Llama 3, Mistral) to perform quantitative and qualitative risk assessments on cryptocurrency assets.

## 🚀 Features

* **Asynchronous Data Fetching:** High-performance data retrieval from CoinGecko API.
* **Local LLM Inference:** Uses RTX A2000 GPU for offline, private analysis.
* **RAG (Retrieval-Augmented Generation):** Learns from a local knowledge base of scam patterns.
* **Professional Reporting:** Generates PDF audits and Excel portfolio plans.
* **Structured Logging:** Enterprise-grade logging for audit trails.

## 🛠️ Architecture



## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourname/ChainSentinel.git](https://github.com/yourname/ChainSentinel.git)
    cd ChainSentinel
    ```

2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Setup Configuration:**
    Create a `.env` file (optional) or modify `config/settings.py`.

## 🖥️ Usage

**Run a Token Audit:**
```bash
python src/main.py audit solana