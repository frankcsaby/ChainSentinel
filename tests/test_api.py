import pytest
from unittest.mock import AsyncMock
from src.services.coingecko import CoinGeckoService
from src.core.risk_engine import RiskEngine
from src.services.web_search import WebSearchService
from src.core.llm_engine import LLMEngine

# --- 1. KOCKÁZATI MOTOR TESZT ---
def test_risk_engine_math():
    engine = RiskEngine()
    fake_data = {
        "market_cap_rank": 1,
        "market_data": {
            "price_change_percentage_24h": 1.0,
            "total_volume": {"usd": 1000},
            "market_cap": {"usd": 50000}
        },
        "developer_data": {"stars": 1500}
    }
    
    result = engine.calculate_risk_metrics(fake_data)
    assert result['quantitative_score'] < 50
    assert result['metrics']['liquidity_ratio'] == 1000 / 50000

# =====================================================================
# GOLYÓÁLLÓ AIOHTTP MOCK OSZTÁLYOK
# (Ezek garantáltan nem dobnak 'coroutine' hibát az async with blokkban)
# =====================================================================
class DummyAiohttpResponse:
    def __init__(self):
        self.status = 200
        
    async def json(self):
        return {"name": "MockCoin", "symbol": "MCK"}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyAiohttpSession:
    def __init__(self, *args, **kwargs):
        pass
        
    def get(self, url, **kwargs):
        return DummyAiohttpResponse()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
# =====================================================================

# --- 2. COINGECKO API MOCKOLÁSA (JAVÍTOTT VERZIÓ) ---
@pytest.mark.asyncio
async def test_coingecko_service_mocked(mocker):
    service = CoinGeckoService()
    
    # A kritikus lépés: Kicseréljük az EREDETI aiohttp.ClientSession-t 
    # a mi kis saját, hibamentes Dummy osztályunkra.
    mocker.patch("aiohttp.ClientSession", new=DummyAiohttpSession)
    
    data = await service.get_coin_data("mockcoin")
    
    assert data is not None
    assert data["name"] == "MockCoin"

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