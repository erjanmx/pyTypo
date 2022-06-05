from tinydb import Query, TinyDB


class TinyDBProvider:
    def __init__(self, db_path: str):
        self.db = TinyDB(db_path)
        self.query = Query()

    def close(self):
        self.db.close()

    def add_to_approved(self, repository_name: str, typo: str, suggested: str):
        self.db.insert(
            {
                "repo": repository_name.lower(),
                "typo": typo.lower(),
                "suggested": suggested.lower(),
            }
        )

    def add_to_ignored(self, word: str):
        if not self.is_ignored(word):
            self.db.insert({"word": word.lower()})

    def is_ignored(self, word):
        return self.db.search(self.query.word == word.lower())

    def is_already_approved_repo(self, repository_name):
        return self.db.search(self.query.repo == repository_name.lower())
