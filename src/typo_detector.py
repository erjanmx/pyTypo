import logging
import os
import re

import inflect
from autocorrect import Speller

MAX_TYPO_OCCURRENCES = 2
WORDS_REGEX = "^[a-z]{4,}$"
PATH = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


class TypoDetector:
    def __init__(self, speller=None):
        self.inflect = inflect.engine()
        self.speller = speller if speller else Speller()

        self.words = self.load_words()

    @staticmethod
    def load_words():
        with open(os.path.join(PATH, "../data/words_alpha.txt")) as word_file:
            valid_words = set(word_file.read().split())

        return valid_words

    @staticmethod
    def get_unique_words(text: str) -> list:
        return list(
            set(filter(lambda w: re.search(WORDS_REGEX, w) is not None, text.split()))
        )

    def is_possible_typo(self, word: str) -> bool:
        if word in self.words:
            return False

        autocorrected_word = self.speller.autocorrect_word(word)

        def variant(word_1, word_2, prefix="", suffix=""):
            return (
                f"{prefix}{word_1}{suffix}".lower() == word_2.lower()
                or f"{prefix}{word_2}{suffix}".lower() == word_1.lower()
            )

        # story - stories
        if (
            self.inflect.plural(word) == autocorrected_word
            or self.inflect.plural(autocorrected_word) == word
        ):
            return False

        # set - unset
        if variant(word, autocorrected_word, prefix="un"):
            return False

        # placed - replaced
        if variant(word, autocorrected_word, prefix="re"):
            return False

        # compress - decompress
        if variant(word, autocorrected_word, prefix="de"):
            return False

        # complete - incomplete
        if variant(word, autocorrected_word, prefix="in"):
            return False

        # strong - strongly
        if variant(word, autocorrected_word, suffix="ly"):
            return False

        # force - forced
        if variant(word, autocorrected_word, suffix="d"):
            return False

        return word != autocorrected_word

    def get_possible_typos_with_suggestions(self, text: str) -> dict:
        words = self.get_unique_words(text)

        possible_typos = {}
        for word in words:
            if self.is_possible_typo(word):
                possible_typos[word] = self.speller.autocorrect_word(word)

        return possible_typos

    def get_typos_with_suggestions(self, text: str) -> dict:
        words = self.get_unique_words(text)

        typos = {}
        for word in words:
            if self.is_typo(word):
                typos[word] = self.speller.autocorrect_word(word)

        return typos
