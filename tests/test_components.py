import pytest
from src.core.rag_engine import RAGEngine
from src.services.news import NewsService
from src.utils.report_gen import ReportGenerator
import os

# 1. Teszteljük, hogy a RAG motor be tudja-e tölteni a fájlokat
def test_rag_engine_loading():
    rag = RAGEngine()
    # Hozzunk létre egy ideiglenes teszt fájlt
    test_file = "data/knowledge_base/test_knowledge.txt"
    with open(test_file, "w") as f:
        f.write("Test knowledge content")
    
    context = rag.load_context()
    
    assert "Test knowledge content" in context
    assert "--- KNOWLEDGE SOURCE:" in context
    
    # Takarítás
    os.remove(test_file)

# 2. Teszteljük, hogy a Hírek modul ad-e vissza szöveget
def test_news_service():
    news = NewsService()
    result = news.get_latest_news("Bitcoin")
    
    assert isinstance(result, str)
    assert len(result) > 0

# 3. Teszteljük a PDF generálást
def test_pdf_generation():
    dummy_data = {
        "verdict": "Safe",
        "score": 90,
        "summary": "This is a test summary.",
        "pros": ["Good tech"],
        "cons": ["High volatility"]
    }
    
    path = ReportGenerator.create_pdf(dummy_data, "TestToken")
    
    assert path is not None
    assert os.path.exists(path)
    
    # Takarítás (opcionális, ha látni akarod a fájlt, vedd ki)
    # os.remove(path)