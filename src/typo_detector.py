import logging
import re

from autocorrect import Speller

MAX_TYPO_OCCURRENCES = 2
WORDS_REGEX = "^[a-zA-Z]{4,}$"

logger = logging.getLogger(__name__)


class TypoDetector:
    def __init__(self, speller=None):
        self.speller = speller if speller else Speller()

    @staticmethod
    def get_unique_words(text: str) -> list:
        return list(
            set(filter(lambda w: re.search(WORDS_REGEX, w) is not None, text.split()))
        )

    def is_possible_typo(self, word) -> bool:
        return word != self.speller.autocorrect_word(word)

    def get_possible_typos(self, text: str) -> dict:
        words = self.get_unique_words(text)

        possible_typos = {}
        for word in words:
            # skip words with uppercase anywhere but first letter
            if 0 < sum(1 for letter in word[1:] if letter.isupper()):
                continue

            if self.is_possible_typo(word):
                if text.count(word) > MAX_TYPO_OCCURRENCES:
                    logger.info(
                        f'Too many occurrences of possible typo "{word}" in text - {text.count(word)}'
                    )
                    continue

                possible_typos[word] = self.speller.autocorrect_word(word)

        return possible_typos
