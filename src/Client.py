import re
import logging
from github3.repos import Repository
from github3.pulls import PullRequest
from src.action import Action
from src.typo import Typo
from src.database import TinyDBProvider
from src.github_client import GithubClient
from src.typo_detector import TypoDetector
from src.language_detector import LanguageDetector

logger = logging.getLogger(__name__)

EMPTY_DICT = {}
ACTION_SKIP_WORD = "action-skip-word"
ACTION_SKIP_REPO = "action-skip-repo"
ACTION_IGNORE_WORD = "action-ignore-word"
ACTION_APPROVE_REPO = "action-approve-typo"


class Client:
    def __init__(self, github: GithubClient, database: TinyDBProvider):
        self.github = github
        self.database = database
        self.typo_detector = TypoDetector()
        self.language_detector = LanguageDetector()

    def get_repos(self, date):
        return self.github.get_most_starred_repos_for_date(date)

    def get_repo_typo(self, date):
        repos = self.get_repos(date)

        for repo in repos:
            repository = repo.repository

            if self.database.is_already_approved_repo(repository.full_name):
                logger.info("Already had PR")
                continue

            readme = self.github.get_repository_readme(repository)

            if readme == "":
                continue

            if not self.language_detector.is_english(readme):
                logger.info("Readme is not in English")
                continue

            suggestions = self.typo_detector.get_possible_typos(readme)

            for maybe_typo, suggestion in suggestions.items():
                # skip if the "typo" word is in repo name
                if maybe_typo.lower() in repository.full_name.lower():
                    logger.info('Repo name contains the word "%s"', maybe_typo)
                    continue

                if self.database.is_ignored(maybe_typo):
                    logger.info('"%s" is in ignore list', maybe_typo)
                    continue

                typo = Typo(
                    repository=repository.full_name,
                    readme=readme,
                    word=maybe_typo,
                    suggested=suggestion,
                )
                action = yield typo

                if action == Action.IGNORE_WORD.value:
                    self.ignore_word(maybe_typo)
                elif action in [Action.SKIP_REPO.value, ACTION_APPROVE_REPO]:
                    break

    def ignore_word(self, word: str):
        logger.info(f"Adding {word} to ignore list")
        self.database.add_to_ignored(word)

    def create_pull_request(self, typo: Typo) -> PullRequest:
        readme = self.github.get_repository_readme(typo.repository)
        modified_readme = re.sub(r"\b%s\b" % typo.word, typo.suggested, readme)

        # print('pull request')
        # return

        return self.github.create_fix_typo_pull_request(
            typo.repository, modified_readme=modified_readme
        )
