import logging
from tinydb import Query, TinyDB

logger = logging.getLogger(__name__)


class TinyDBProvider:
    def __init__(self, db_path: str):
        self.db = TinyDB(db_path)
        self.query = Query()

    def close(self):
        self.db.close()

    def add_to_approved(self, repository_name: str, typo: str, suggested: str) -> int:
        logger.info(f'Adding "{repository_name}" to approved repo list')
        return self.db.insert(
            {
                "repo": repository_name.lower(),
                "typo": typo.lower(),
                "suggested": suggested.lower(),
            }
        )

    def add_to_ignored(self, word: str):
        if not self.is_ignored(word):
            logger.info(f'Adding "{word}" to ignore list')
            self.db.insert({"word": word.lower()})

    def is_ignored(self, word):
        return self.db.search(self.query.word == word.lower())

    def is_already_approved_repo(self, repository_name):
        return self.db.search(self.query.repo == repository_name.lower())
