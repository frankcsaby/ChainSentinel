import pytest
from unittest.mock import AsyncMock
from src.services.coingecko import CoinGeckoService
from src.core.risk_engine import RiskEngine
from src.services.web_search import WebSearchService
from src.core.llm_engine import LLMEngine

# --- 1. KOCKÁZATI MOTOR TESZT (FRISSÍTVE AZ 5 DIMENZIÓHOZ) ---
def test_risk_engine_math():
    engine = RiskEngine()
    
    # Bővítettük a tesztadatot a közösségi mutatókkal is
    fake_data = {
        "market_cap_rank": 1,
        "market_data": {
            "price_change_percentage_24h": 1.0,
            "total_volume": {"usd": 1000},
            "market_cap": {"usd": 50000}
        },
        "developer_data": {"stars": 1500},
        "community_data": {"twitter_followers": 100000}
    }
    
    result = engine.calculate_risk_metrics(fake_data)
    
    # Ellenőrizzük az új adatszerkezetet
    assert "quantitative_score" in result
    assert "dimensions" in result
    
    # A kockázatnak 50 alatt kell lennie (stabil coin)
    assert result['quantitative_score'] < 50
    
    # Ellenőrizzük, hogy mind az 5 dimenziót kiszámolta-e a Radar Chart-hoz
    dims = result['dimensions']
    assert "Volatility Safety" in dims
    assert "Liquidity Strength" in dims
    assert "Market Position" in dims
    assert "Development" in dims
    assert "Community" in dims

# =====================================================================
# GOLYÓÁLLÓ AIOHTTP MOCK OSZTÁLYOK (FRISSÍTVE A HISTORY ADATOKHOZ)
# =====================================================================
class DummyAiohttpResponse:
    def __init__(self, is_history=False):
        self.status = 200
        self.is_history = is_history
        
    async def json(self):
        # Ha történeti adatokat kér a grafikonhoz:
        if self.is_history:
            return {"prices": [[1600000000, 50000], [1600086400, 51000]]}
        # Ha alap adatokat kér:
        return {"name": "MockCoin", "symbol": "MCK"}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyAiohttpSession:
    def __init__(self, *args, **kwargs):
        pass
        
    def get(self, url, **kwargs):
        # Megnézzük, hogy a normál vagy a grafikonos (market_chart) végpontot hívja-e
        is_history = "market_chart" in url
        return DummyAiohttpResponse(is_history=is_history)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
# =====================================================================

# --- 2. COINGECKO API MOCKOLÁSA (KIBŐVÍTVE) ---
@pytest.mark.asyncio
async def test_coingecko_service_mocked(mocker):
    service = CoinGeckoService()
    
    # Kicseréljük az aiohttp.ClientSession-t a saját Mock-unkra
    mocker.patch("aiohttp.ClientSession", new=DummyAiohttpSession)
    
    # 2.A: Normál adat letöltésének tesztelése
    data = await service.get_coin_data("mockcoin")
    assert data is not None
    assert data["name"] == "MockCoin"
    
    # 2.B: Történelmi árak letöltésének tesztelése (ÚJ)
    history = await service.get_historical_prices("mockcoin", days=30)
    assert len(history) == 2
    assert history[0] == 50000

# --- 3. WEB SEARCH MOCKOLÁSA ---
@pytest.mark.asyncio
async def test_web_search_async(mocker):
    service = WebSearchService()
    
    mocker.patch.object(service, '_search_sync', return_value="1. [Test Hack] - Fake news")
    
    result = await service.search_news("TestToken")
    assert "Test Hack" in result

# --- 4. LLM ENGINE MOCKOLÁSA ---
@pytest.mark.asyncio
async def test_llm_engine_mocked(mocker):
    engine = LLMEngine()
    
    mock_ollama_response = {'message': {'content': '{"verdict": "Safe", "score": 90}'}}
    mocker.patch('ollama.AsyncClient.chat', new_callable=AsyncMock, return_value=mock_ollama_response)
    
    result = await engine.analyze_json("Test prompt", "Test system prompt")
    
    assert "error" not in result
    assert result["verdict"] == "Safe"
    assert result["score"] == 90