import logging
from django.conf import settings
from .exceptions import LLMGenerationError
import google.genai as genai

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        logger.info("Initializing GeminiClient")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate(self, prompt: str, request_id: str | None = None) -> str:
        try:
            logger.info("Sending prompt to Gemini", extra={"request_id": request_id})

            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )

            text = response.text

            if not text:
                raise LLMGenerationError("Empty response from Gemini")

            logger.info("Gemini response received", extra={"request_id": request_id})
            return text.strip()

        except Exception as e:
            logger.exception("Gemini generation failed", extra={"request_id": request_id})
            raise LLMGenerationError(str(e))
