import ollama
import json
from typing import Dict, Any
from loguru import logger
from config.settings import settings

class LLMEngine:
    def __init__(self):
        self.model = settings.MODEL_NAME

    def analyze_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Kényszerített JSON választ kér az LLM-től.
        """
        try:
            logger.debug("LLM Elemzés indítása...")
            response = ollama.chat(
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