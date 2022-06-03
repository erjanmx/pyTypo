import unittest
from src.typo_detector import TypoDetector
from autocorrect import Speller


class TestTypoDetector(unittest.TestCase):
    def test_get_unique_words(self):
        detector = TypoDetector()

        self.assertCountEqual(
            detector.get_unique_words('Here is a sample text to be split'),
            ['Here', 'text', 'split', 'sample']
        )

    def test_get_possible_typos(self):
        detector = TypoDetector()

        test_text = "I'm not sleapy and tehre is no place I'm giong to."
        expected_typos = {'giong': 'going', 'sleapy': 'sleepy', 'tehre': 'there'}

        self.assertEqual(expected_typos, detector.get_possible_typos(test_text))


if __name__ == '__main__':
    unittest.main()
