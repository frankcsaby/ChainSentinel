import ollama
import json
from typing import Dict, Any
from loguru import logger
from config.settings import settings

class LLMEngine:
    def __init__(self):
        self.model = settings.MODEL_NAME
        # Async kliens inicializálása
        self.client = ollama.AsyncClient()

    async def analyze_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Aszinkron LLM hívás JSON kimenettel.
        """
        try:
            logger.debug("Aszinkron LLM Elemzés indítása...")
            response = await self.client.chat(
                model=self.model,
                format='json',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return json.loads(response['message']['content'])
        except json.JSONDecodeError:
            logger.error("Az LLM nem valid JSON-t küldött.")
            return {"error": "Invalid JSON response"}
        except Exception as e:
            logger.exception(f"LLM Hiba: {e}")
            return {"error": str(e)}