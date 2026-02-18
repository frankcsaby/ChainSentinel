import os
from pathlib import Path
from loguru import logger
from config.settings import settings

class RAGEngine:
    def __init__(self):
        self.kb_path = settings.KNOWLEDGE_BASE_DIR

    def load_context(self) -> str:
        """
        Beolvassa az összes .txt fájlt a knowledge_base mappából,
        és egyetlen nagy szöveggé fűzi össze a kontextushoz.
        """
        context_text = ""
        try:
            if not self.kb_path.exists():
                logger.warning(f"Tudásbázis mappa nem található: {self.kb_path}")
                return "No external knowledge base available."

            files = list(self.kb_path.glob("*.txt"))
            if not files:
                logger.warning("A tudásbázis mappa üres.")
                return "No external knowledge base available."

            logger.info(f"{len(files)} tudásbázis fájl beolvasása...")
            
            for file_path in files:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    context_text += f"\n--- KNOWLEDGE SOURCE: {file_path.name} ---\n{content}\n"
            
            return context_text

        except Exception as e:
            logger.error(f"Hiba a tudásbázis olvasásakor: {e}")
            return "Error loading knowledge base."