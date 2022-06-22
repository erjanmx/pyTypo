import logging
import re

import inflect
from autocorrect import Speller

MAX_TYPO_OCCURRENCES = 2
WORDS_REGEX = "^[a-zA-Z]{4,}$"

logger = logging.getLogger(__name__)


class TypoDetector:
    def __init__(self, speller=None):
        self.inflect = inflect.engine()
        self.speller = speller if speller else Speller()

    @staticmethod
    def get_unique_words(text: str) -> list:
        return list(
            set(filter(lambda w: re.search(WORDS_REGEX, w) is not None, text.split()))
        )

    def is_possible_typo(self, word: str) -> bool:
        autocorrected_word = self.speller.autocorrect_word(word)

        if (
            self.inflect.plural(word) == autocorrected_word
            or self.inflect.plural(autocorrected_word) == word
        ):
            return False

        if (
            f"un{word}".lower() == autocorrected_word.lower()
            or f"un{autocorrected_word}".lower() == word.lower()
        ):
            return False

        if (
            f"re{word}".lower() == autocorrected_word.lower()
            or f"re{autocorrected_word}".lower() == word.lower()
        ):
            return False

        if (
            f"de{word}".lower() == autocorrected_word.lower()
            or f"de{autocorrected_word}".lower() == word.lower()
        ):
            return False

        if (
            f"{word}ly".lower() == autocorrected_word.lower()
            or f"{autocorrected_word}ly".lower() == word.lower()
        ):
            return False

        if (
            f"{word}d".lower() == autocorrected_word.lower()
            or f"{autocorrected_word}d".lower() == word.lower()
        ):
            return False

        return word != autocorrected_word

    def get_possible_typos_with_suggestions(self, text: str) -> dict:
        words = self.get_unique_words(text)

        possible_typos = {}
        for word in words:
            # skip words with uppercase anywhere but first letter
            if 0 < sum(1 for letter in word[1:] if letter.isupper()):
                continue

            if self.is_possible_typo(word):
                possible_typos[word] = self.speller.autocorrect_word(word)

                # first_candidate, confidence = Word(word).spellcheck()[0]
                # if word != first_candidate and confidence > 0.9:
                #     possible_typos[word] = self.speller.autocorrect_word(word)

        return possible_typos
