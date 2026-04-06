import logging
import os

from .typo_detector import TypoDetector

PATH = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


class TypoDetectorDict(TypoDetector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.common_typos = self._load_typos()

    @staticmethod
    def _load_typos():
        typos = {}
        with open(os.path.join(PATH, "../data/common_typos.txt")) as word_file:
            for line in word_file:
                if len(line.strip().split(':')) == 2:
                    typo, correct = line.strip().split(':')
                    typos[typo.strip()] = correct.strip()

        return typos

    def get_possible_typos_with_suggestions(self, text: str) -> dict:
        words = self.get_unique_words(text)

        possible_typos = {}
        for word in words:
            if word in self.common_typos and word != self.common_typos[word]:
                possible_typos[word] = self.common_typos[word]

        return possible_typos
