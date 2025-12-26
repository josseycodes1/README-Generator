import logging
from django.conf import settings
from .exceptions import LLMGenerationError
import google.genai as genai

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate(self, prompt: str) -> str:
        try:
            logger.info("Sending prompt to Gemini")


            response = self.client.text.generate(
                model="gemini-1.5-flash",
                prompt=prompt
            )

            if not response or not response.output_text:
                raise LLMGenerationError("Empty response from Gemini")

            return response.output_text.strip()

        except Exception as e:
            logger.exception("Gemini generation failed")
            raise LLMGenerationError(str(e))
