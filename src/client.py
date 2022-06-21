import logging
import re

from github3.pulls import PullRequest

from src.action import Action
from src.database import TinyDBProvider
from src.github_client import GithubClient
from src.language_detector import LanguageDetector
from src.typo import Typo
from src.typo_detector import TypoDetector

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, github: GithubClient, database: TinyDBProvider):
        self.github = github
        self.database = database
        self.typo_detector = TypoDetector()
        self.language_detector = LanguageDetector()

    def get_repo_typo(self, date):
        repositories = self.github.get_most_starred_repos_for_date(date)

        for repo in repositories:
            repository = repo.repository

            if self.database.is_already_approved_repo(repository.full_name):
                logger.debug(f'Already had PR in "{repository.full_name}" repo, skipping')
                continue

            readme = self.github.get_repository_readme(repository)

            if readme == "":
                logger.debug("Readme is empty, skipping")
                continue

            if not self.language_detector.is_english(readme):
                logger.debug("Readme is not in English, skipping")
                continue

            suggestions = self.typo_detector.get_possible_typos_with_suggestions(readme)

            for maybe_typo, suggestion in suggestions.items():
                # skip if the "typo" word is in repo name
                if maybe_typo.lower() in repository.full_name.lower():
                    logger.debug('Repo name contains the word "%s"', maybe_typo)
                    continue

                if self.database.is_ignored(maybe_typo):
                    logger.debug('"%s" is in ignore list', maybe_typo)
                    continue

                if len(repository.full_name + maybe_typo + suggestion) > 54:
                    logger.debug(f'Repo name "{repository.full_name}" is too long')
                    continue

                typo = Typo(
                    repository=repository.full_name,
                    readme=readme,
                    word=maybe_typo,
                    suggested=suggestion,
                )

                action = yield typo

                if action == Action.IGNORE_WORD:
                    self.database.add_to_ignored(maybe_typo)
                elif action in [Action.SKIP_REPO, Action.APPROVE_REPO]:
                    break

    def create_pull_request(self, typo: Typo) -> PullRequest:
        readme = self.github.get_repository_readme(typo.repository)
        modified_readme = re.sub(r"\b%s\b" % typo.word, typo.suggested, readme)

        return self.github.create_fix_typo_pull_request(
            typo.repository, modified_readme=modified_readme
        )

    def approve_typo(self, typo: Typo):
        self.create_pull_request(typo)
        self.database.add_to_approved(
            typo.repository, typo=typo.word, suggested=typo.suggested
        )

    def delete_fork_repository(self, repository: str):
        _, repo_name = repository.split("/")
        fork_repo_name = f"{self.github.get_me()}/{repo_name}"
        return self.github.delete_repository(fork_repo_name)
