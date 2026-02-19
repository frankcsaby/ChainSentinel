import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.coingecko import CoinGeckoService
from src.core.risk_engine import RiskEngine
from src.services.web_search import WebSearchService
from src.core.llm_engine import LLMEngine

# --- 1. KOCKÁZATI MOTOR (Nincs szükség hálózatra) ---
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
    assert result['quantitative_score'] < 50  # Stabil projektnek kell lennie
    assert result['metrics']['liquidity_ratio'] == 1000 / 50000

# --- 2. COINGECKO API MOCKOLÁSA (JAVÍTOTT VERZIÓ) ---
@pytest.mark.asyncio
async def test_coingecko_service_mocked(mocker):
    service = CoinGeckoService()
    
    # Szimuláljuk a sikeres HTTP választ
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"name": "MockCoin", "symbol": "MCK"}
    
    # Javítás: Helyesen mockoljuk az `async with session.get(...)` részt
    mock_get = AsyncMock()
    mock_get.__aenter__.return_value = mock_response
    
    # Javítás: Helyesen mockoljuk az `async with aiohttp.ClientSession()` részt
    mock_session = AsyncMock()
    mock_session.get.return_value = mock_get
    mock_session.__aenter__.return_value = mock_session
    
    # Kicseréljük az aiohttp.ClientSession-t a saját Mock-unkra
    mocker.patch("aiohttp.ClientSession", return_value=mock_session)
    
    # Teszteljük a függvényt
    data = await service.get_coin_data("mockcoin")
    
    # Ellenőrizzük az eredményt
    assert data is not None
    assert data["name"] == "MockCoin"

# --- 3. WEB SEARCH MOCKOLÁSA ---
@pytest.mark.asyncio
async def test_web_search_async(mocker):
    service = WebSearchService()
    
    # Kicseréljük a belső _search_sync függvényt, hogy azonnal visszatérjen
    mocker.patch.object(service, '_search_sync', return_value="1. [Test Hack] - Fake news")
    
    result = await service.search_news("TestToken")
    assert "Test Hack" in result

# --- 4. LLM ENGINE MOCKOLÁSA ---
@pytest.mark.asyncio
async def test_llm_engine_mocked(mocker):
    engine = LLMEngine()
    
    # Szimuláljuk a sikeres JSON választ az Ollamától
    mock_ollama_response = {'message': {'content': '{"verdict": "Safe", "score": 90}'}}
    
    # Mockoljuk az AsyncClient.chat hívást
    mocker.patch('ollama.AsyncClient.chat', new_callable=AsyncMock, return_value=mock_ollama_response)
    
    result = await engine.analyze_json("Test prompt", "Test system prompt")
    
    assert "error" not in result
    assert result["verdict"] == "Safe"
    assert result["score"] == 90