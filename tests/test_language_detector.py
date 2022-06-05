import unittest

from src.language_detector import LanguageDetector


class TestLanguageDetector(unittest.TestCase):
    def test_detect(self):
        detector = LanguageDetector()

        self.assertEqual(detector.detect('Sample text here'), 'en')
        self.assertEqual(detector.detect('Текст для проверки'), 'ru')

    def test_is_english(self):
        detector = LanguageDetector()

        self.assertTrue(detector.is_english('Launching unittests with arguments'))
        self.assertFalse(detector.is_english('Запуск тестирования с аргументами'))


if __name__ == '__main__':
    unittest.main()
