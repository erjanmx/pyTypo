import string

MAX_WORDS_COUNT = 2
STOP_CHARS = [".", ",", "!", "?", ":", ";", "|", "*", "#", "(", ")", "<", ">", "\n"]


class RepoReadmeTypo:
    id: int = None

    def __init__(self, repository: str, word: str, suggested: str, readme: str = None):
        self.repository = repository
        self.word = word
        self.readme = readme
        self.suggested = suggested

    def get_context(self) -> (str, str):
        # get position of the word in text
        typo_at = self.readme.find(self.word)

        # get MAX_WORDS_COUNT words prior to typo-word in text
        context_head = ""
        for char in self.readme[:typo_at][::-1]:
            if char in STOP_CHARS or (
                char in string.whitespace
                and len(context_head.split()) > MAX_WORDS_COUNT
            ):
                break
            context_head = char + context_head

        # get MAX_WORDS_COUNT words after the typo-word in text
        context_tail = ""
        for char in self.readme[typo_at + len(self.word) :]:
            if char in STOP_CHARS or (
                char in string.whitespace
                and len(context_tail.split()) > MAX_WORDS_COUNT
            ):
                break
            context_tail = context_tail + char

        return f"{context_head.strip()} *{self.word}* {context_tail.strip()}".strip()

    def get_word_readme_occurrence_count(self):
        return self.readme.count(self.word)
