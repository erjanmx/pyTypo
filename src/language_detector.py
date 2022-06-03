from langdetect import detect


class LanguageDetector:
    @staticmethod
    def detect(text: str) -> str:
        return detect(text)

    def is_english(self, text: str) -> bool:
        return self.detect(text) == 'en'
