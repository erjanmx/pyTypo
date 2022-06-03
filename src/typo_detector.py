import re
from autocorrect import Speller


class TypoDetector:
    words_regex = '^[a-zA-Z]{4,}$'

    def __init__(self):
        self.speller = Speller()

    def get_unique_words(self, text: str) -> list:
        return list(set(filter(lambda w: re.search(self.words_regex, w) is not None, text.split())))

    def is_possible_typo(self, word) -> bool:
        return word != self.speller.autocorrect_word(word)

    def get_possible_typos(self, text: str) -> dict:
        words = self.get_unique_words(text)

        possible_typos = {}
        for word in words:
            if self.is_possible_typo(word):
                possible_typos[word] = self.speller.autocorrect_word(word)

        return possible_typos
