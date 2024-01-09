import string

MAX_WORDS_COUNT = 2
STOP_CHARS = [
    ".",
    ",",
    "!",
    "?",
    ":",
    ";",
    "|",
    "*",
    "#",
    "(",
    ")",
    "<",
    ">",
    "[",
    "]",
    "\n",
]


class RepoReadmeTypo:
    id: int = None

    def __init__(self, repository: str, word: str, suggested: str, readme: str = None):
        self.repository = repository
        self.readme = readme
        self.maybe_typo = word
        self.suggested_word = suggested

    def get_typo_with_context(self) -> str:
        """
        Get typo word with some words around it in text

        :return: str
        """
        # get position of the word in text
        typo_at = self.readme.find(self.maybe_typo)

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
        for char in self.readme[typo_at + len(self.maybe_typo) :]:
            if char in STOP_CHARS or (
                char in string.whitespace
                and len(context_tail.split()) > MAX_WORDS_COUNT
            ):
                break
            context_tail = context_tail + char

        return (
            f"{context_head.strip()} {self.maybe_typo} {context_tail.strip()}".strip()
        )

    def get_word_readme_occurrence_count(self) -> int:
        """
        Count how many times typo-word occurs in readme
        :return: int
        """
        return self.readme.count(self.maybe_typo)
