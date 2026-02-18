import pytest
import pytest_asyncio
from src.services.coingecko import CoinGeckoService
from src.core.risk_engine import RiskEngine
from src.services.web_search import WebSearchService

# --- 1. KOCKÁZATI MOTOR TESZT ---
def test_risk_calculation():
    """Teszteli, hogy a matek helyes-e."""
    engine = RiskEngine()
    
    # Mock adat: Egy biztonságos coin (pl. Bitcoin)
    safe_data = {
        "market_cap_rank": 1,
        "market_data": {
            "price_change_percentage_24h": 1.5,
            "total_volume": {"usd": 50000000},
            "market_cap": {"usd": 1000000000}
        },
        "developer_data": {"stars": 50000}
    }
    
    result = engine.calculate_risk_metrics(safe_data)
    
    # A Bitcoin kockázatának alacsonynak kell lennie ( < 50)
    assert result["quantitative_score"] < 50
    assert "liquidity_ratio" in result["metrics"]

# --- 2. WEB SEARCH TESZT ---
def test_web_search():
    """Teszteli, hogy a kereső ad-e vissza szöveget."""
    service = WebSearchService()
    result = service.search_news("Ethereum")
    
    assert isinstance(result, str)
    assert len(result) > 0
    # Ellenőrizzük, hogy nem hibaüzenet jött-e vissza (ha van net)
    if "unavailable" not in result:
        print(f"\nKeresési eredmény minta: {result[:50]}...")

# --- 3. API TESZT (Async) ---
@pytest.mark.asyncio
async def test_coingecko_api():
    """Teszteli, hogy a CoinGecko API elérhető-e."""
    service = CoinGeckoService()
    
    data = await service.get_coin_data("bitcoin")
    
    assert data is not None
    assert data["name"] == "Bitcoin"
    assert "market_data" in data