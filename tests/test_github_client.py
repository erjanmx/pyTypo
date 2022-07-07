import unittest
from unittest.mock import patch

from src.github_client import GithubClient


class TestGithubClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = GithubClient("")

    def test_get_repo_link(self):
        self.assertEqual(
            "https://github.com/test/repo", self.client.get_repo_link("test/repo")
        )

    @patch("src.github_client.GitHub")
    def test_get_me(self, mock_gh):
        mock_gh().me.return_value = "erjanmx"
        client = GithubClient("")

        self.assertEqual("erjanmx", client.get_me())


if __name__ == "__main__":
    unittest.main()
