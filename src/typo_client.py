import datetime
import logging
import re
from collections import Counter

from github3.exceptions import NotFoundError, UnavailableForLegalReasons
from github3.pulls import PullRequest
from github3.repos.repo import Repository

from src.action import Action
from src.database import TinyDBProvider
from src.github_client import TYPO_BRANCH_NAME, GithubClient
from src.language_detector import LanguageDetector
from src.repo_readme_typo import RepoReadmeTypo
from src.typo_detector import MAX_TYPO_OCCURRENCES, TypoDetector

logger = logging.getLogger(__name__)

MIN_REPO_STARS = 30  # minimum amount of stargazers of the repo to be checked for typos
DAYS_TO_LOOK_BACK = 7
MIN_OCCURRENCE_COUNT_TO_IGNORE = 50


class TypoClient:
    look_date = None
    repo_generator = None

    def __init__(
        self,
        github: GithubClient,
        database: TinyDBProvider,
        typo_detector: TypoDetector,
    ):
        self.github = github
        self.database = database
        self.typo_detector = typo_detector
        self.counter = Counter()
        self.language_detector = LanguageDetector()

        self.reset_generator()
        self.reset_look_date()

    def get_repo_typo(self, date):
        repositories = self.github.get_most_starred_repos_for_date(date)

        for repo in repositories:
            repository: Repository = repo.repository

            if repository.stargazers_count < MIN_REPO_STARS:
                logger.debug("Repo does not meet min stars requirement, skipping")
                break  # repos are sorted desc by stars so there is no point looking further

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

                if self.check_counter(maybe_typo, readme):
                    logger.info(
                        f'Too many occurrences of word "{maybe_typo}" in total - '
                        f"{self.counter.get(maybe_typo.lower())}, adding to ignore list"
                    )
                    self.add_to_ignored(maybe_typo)
                    continue

                typo = RepoReadmeTypo(
                    repository=repository.full_name,
                    readme=readme,
                    word=maybe_typo,
                    suggested=suggestion,
                )

                if typo.get_word_readme_occurrence_count() > MAX_TYPO_OCCURRENCES:
                    logger.debug(
                        f'Too many occurrences of possible typo "{maybe_typo}" '
                        f"in text - {readme.count(maybe_typo)}, skipping"
                    )
                    continue

                if not self.language_detector.is_english(typo.get_typo_with_context()):
                    logger.debug("Typo context is not in English, skipping")
                    continue

                if len(repository.full_name + maybe_typo + suggestion) > 54:  # fixme
                    logger.debug(f'Repo name "{repository.full_name}" is too long')
                    break

                action = yield typo

                if action in [Action.SKIP_REPO, Action.APPROVE_REPO]:
                    break

    def check_counter(self, word: str, readme: str) -> bool:
        """
        Keep track of most frequent words across all repos

        :param word: str
        :param readme: str
        :return: bool
        """
        word_lower = word.lower()

        self.counter.update([word_lower] * readme.lower().count(word_lower))

        can_ignore = self.counter.get(word_lower) >= MIN_OCCURRENCE_COUNT_TO_IGNORE

        if can_ignore:
            self.counter.pop(word_lower)

        return can_ignore

    def create_pull_request_with_fix(self, typo: RepoReadmeTypo) -> PullRequest:
        readme = self.github.get_repository_readme(typo.repository)
        modified_readme = re.sub(
            r"\b%s\b" % typo.maybe_typo, typo.suggested_word, readme
        )

        return self.github.create_fix_typo_pull_request(
            typo.repository, modified_readme=modified_readme
        )

    def reset_generator(self):
        self.repo_generator = None

    def reset_look_date(self):
        self.look_date = datetime.datetime.now() - datetime.timedelta(
            days=DAYS_TO_LOOK_BACK
        )

    def init_generator(self):
        if self.repo_generator:
            return

        self.repo_generator = self.get_repo_typo(self.get_date())

    def delete_fork_repository(self, repository: str) -> bool:
        return self.github.delete_fork_repository(repository)

    def get_date(self) -> str:
        return self.look_date.strftime("%Y-%m-%d")

    def lower_look_date(self, offset=1):
        self.reset_generator()
        self.look_date -= datetime.timedelta(days=offset)

    def add_to_ignored(self, word: str):
        return self.database.add_to_ignored(word)

    def add_to_approved(self, typo: RepoReadmeTypo):
        return self.database.add_to_approved(
            typo.repository, typo=typo.maybe_typo, suggested=typo.suggested_word
        )

    def delete_forks_with_closed_pull_requests(self):
        public_repos = self.github.get_my_public_repositories()

        pull_request_head = "{}:{}".format(self.github.get_me(), TYPO_BRANCH_NAME)

        for repo in public_repos:
            if not repo.fork:
                continue
            logger.debug(f'Checking "{repo}" for deletion')

            try:
                repo = repo.refresh()  # get full repo details
                parent_repo = repo.parent

                my_pull_requests = parent_repo.pull_requests(
                    state="closed", number=1, head=pull_request_head
                )
                for _ in my_pull_requests:
                    # PR was closed, we can delete our fork now
                    if self.github.delete_repository(repo):
                        logger.info(f'"{repo}" has been successfully deleted')
                    else:
                        logger.warning(f'Failed to delete fork "{repo}"')
            except (UnavailableForLegalReasons, NotFoundError) as e:
                logger.warning(f'Error "{e}" occurred during deletion of "{repo}"')
