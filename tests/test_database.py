import json
import os
import unittest

from src.database import TinyDBProvider


class TestTinyDBProvider(unittest.TestCase):
    DB_FILE_PATH = "test-db.json"

    def setUp(self) -> None:
        self.db = TinyDBProvider(self.DB_FILE_PATH)

    def tearDown(self) -> None:
        os.remove(self.DB_FILE_PATH)
        self.db.close()

    def test_add_to_approved(self):
        self.db.add_to_approved("approved-repo", "tupo", "typo")

        expected_db_content = {
            "_default": {
                "1": {"repo": "approved-repo", "typo": "tupo", "suggested": "typo"}
            }
        }
        self.assertDictEqual(expected_db_content, self._read_db_raw_content())

    def test_add_to_ignored(self):
        self.db.add_to_ignored("word")
        self.db.add_to_ignored("word")

        expected_db_content = {"_default": {"1": {"word": "word"}}}
        self.assertDictEqual(expected_db_content, self._read_db_raw_content())

    def test_is_ignored(self):
        self.db.add_to_ignored("Ignored")

        self.assertTrue(self.db.is_ignored("ignored"))
        self.assertFalse(self.db.is_ignored("not-ignored"))

    def test_is_already_approved_repo(self):
        self.db.add_to_approved("APPROVED-repo", "tupo", "typo")

        self.assertTrue(self.db.is_already_approved_repo("approved-repo"))
        self.assertFalse(self.db.is_already_approved_repo("repo"))

    def _read_db_raw_content(self):
        with open(self.DB_FILE_PATH, "r") as f:
            return json.loads(f.read())


if __name__ == "__main__":
    unittest.main()
