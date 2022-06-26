import datetime
import logging
import re
from collections import Counter

from github3.pulls import PullRequest

from src.action import Action
from src.database import TinyDBProvider
from src.github_client import GithubClient
from src.language_detector import LanguageDetector
from src.repo_readme_typo import RepoReadmeTypo
from src.typo_detector import MAX_TYPO_OCCURRENCES, TypoDetector

logger = logging.getLogger(__name__)

MIN_OCCURRENCE_COUNT_TO_IGNORE = 50


class Client:
    look_date = None
    repo_generator = None

    def __init__(self, github: GithubClient, database: TinyDBProvider):
        self.github = github
        self.database = database
        self.counter = Counter()
        self.typo_detector = TypoDetector()
        self.language_detector = LanguageDetector()

    def get_repo_typo(self, date):
        repositories = self.github.get_most_starred_repos_for_date(date)

        for repo in repositories:
            repository = repo.repository

            if self.database.is_already_approved_repo(repository.full_name):
                logger.debug(
                    f'Already had PR in "{repository.full_name}" repo, skipping'
                )
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

                if len(repository.full_name + maybe_typo + suggestion) > 54:  # fixme
                    logger.debug(f'Repo name "{repository.full_name}" is too long')
                    continue

                if self.check_counter(maybe_typo, readme):
                    logger.info(
                        f'Too many occurrences of word "{maybe_typo}" in total - '
                        f'{self.counter.get(maybe_typo.lower())}, adding to ignore list'
                    )
                    self.add_to_ignored(maybe_typo)
                    continue

                if readme.count(maybe_typo) > MAX_TYPO_OCCURRENCES:
                    logger.debug(
                        f'Too many occurrences of possible typo "{maybe_typo}" '
                        f'in text - {readme.count(maybe_typo)}, skipping'
                    )
                    continue

                typo = RepoReadmeTypo(
                    repository=repository.full_name,
                    readme=readme,
                    word=maybe_typo,
                    suggested=suggestion,
                )

                if not self.language_detector.is_english(typo.get_context()):
                    logger.debug("Typo context is not in English, skipping")
                    continue

                action = yield typo

                if action in [Action.SKIP_REPO, Action.APPROVE_REPO]:
                    break

    def check_counter(self, word: str, readme: str) -> bool:
        self.counter.update([word.lower()] * readme.lower().count(word.lower()))

        can_ignore = self.counter.get(word.lower()) >= MIN_OCCURRENCE_COUNT_TO_IGNORE

        if can_ignore:
            self.counter.pop(word.lower())

        return can_ignore

    def create_pull_request(self, typo: RepoReadmeTypo) -> PullRequest:
        readme = self.github.get_repository_readme(typo.repository)
        modified_readme = re.sub(r"\b%s\b" % typo.word, typo.suggested, readme)

        return self.github.create_fix_typo_pull_request(
            typo.repository, modified_readme=modified_readme
        )

    def create_pull_request_with_fix(self, typo: RepoReadmeTypo) -> PullRequest:
        pull_request = self.create_pull_request(typo)

        self.database.add_to_approved(
            typo.repository, typo=typo.word, suggested=typo.suggested
        )
        return pull_request

    def delete_fork_repository(self, repository: str):
        _, repo_name = repository.split("/")

        fork_repo_name = f"{self.github.get_me()}/{repo_name}"

        return self.github.delete_repository(fork_repo_name)

    def init(self):
        if self.repo_generator:
            return

        self.look_date = datetime.datetime.now() - datetime.timedelta(days=10)

        self.repo_generator = self.get_repo_typo(self.get_date())

    def get_date(self):
        return self.look_date.strftime("%Y-%m-%d")

    def add_to_ignored(self, word: str):
        self.database.add_to_ignored(word)
