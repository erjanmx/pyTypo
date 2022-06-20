import string

MAX_WORDS_COUNT = 3
STOP_CHARS = [".", ",", "!", "?", ":", ";", "|", "#", "(", ")", "<", ">", "\n"]


class Typo:
    id: int = None

    def __init__(self, repository: str, word: str, suggested: str, readme: str = None):
        self.repository = repository
        self.word = word
        self.readme = readme
        self.suggested = suggested

    def get_context(self) -> (str, str):
        # get position of the word in text
        typo_at = self.readme.find(self.word)

        # get two words prior to typo-word in text
        context_head = ""
        for char in self.readme[:typo_at][::-1]:
            if char in STOP_CHARS or (
                char in string.whitespace
                and len(context_head.split()) >= MAX_WORDS_COUNT
            ):
                break
            context_head = char + context_head

        # get two words after the typo-word in text
        context_tail = ""
        for char in self.readme[typo_at + len(self.word) :]:
            if char in STOP_CHARS or (
                char in string.whitespace
                and len(context_tail.split()) >= MAX_WORDS_COUNT
            ):
                break
            context_tail = context_tail + char

        return context_head.strip(), context_tail.strip()
