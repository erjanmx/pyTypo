import logging

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger(__name__)


class LanguageDetector:
    @staticmethod
    def detect(text: str) -> str:
        try:
            return detect(text)
        except LangDetectException:
            logger.warning("Error detecting language")
        return ""

    def is_english(self, text: str) -> bool:
        return self.detect(text) == "en"
