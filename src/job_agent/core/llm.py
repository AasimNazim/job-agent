import os
import logging
from typing import Any, Type, TypeVar
from google import genai
from pydantic import BaseModel
from ..config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class LLMService:
    """
    Wrapper for Google GenAI API (Gemini).
    Provides structured JSON output capabilities.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. LLM features will fail if called.")
            
        # We assume the user has the google-genai library installed
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        
    def generate_structured_response(self, prompt: str, schema: Type[T]) -> T:
        """
        Sends a prompt to Gemini and enforces a structured JSON response matching the schema.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1 # Low temperature for analytical consistency
                ),
            )
            
            # The google-genai SDK when using response_schema returns a JSON string in response.text
            # Or if it supports structured outputs directly, we parse it.
            # We will use Pydantic to validate and parse the JSON string.
            return schema.model_validate_json(response.text)
            
        except Exception as e:
            logger.error(f"Error generating structured response from LLM: {e}")
            raise
