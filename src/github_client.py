import logging
import urllib.parse
from time import sleep

from github3 import GitHub, exceptions
from github3.pulls import PullRequest
from github3.repos.repo import Repository

logger = logging.getLogger(__name__)
logging.getLogger("github3").setLevel(logging.WARNING)

TYPO_BRANCH_NAME = "fix-readme-typo"
TYPO_COMMIT_MESSAGE = "Fix readme typo"
TYPO_PULL_REQUEST_TITLE = "Fix readme typo"


class GithubClient:
    def __init__(self, token: str):
        self.gh = GitHub(token=token)

    def get_most_starred_repos_for_date(self, date):
        return self.gh.search_repositories(
            "created:{0}..{0}".format(date), order="stars"
        )

    def get_my_public_repositories(self):
        return self.gh.repositories(type="public")

    def get_me(self) -> str:
        return self.gh.me()

    def get_repository_by_name(self, name: str) -> Repository:
        owner, repository_name = name.replace("https://github.com/", "").split("/")

        return self.gh.repository(owner, repository_name)

    def get_repository_readme(self, repository: object) -> str:
        try:
            if isinstance(repository, str):
                repository = self.get_repository_by_name(repository)

            return repository.readme().decoded.decode("utf-8")
        except exceptions.NotFoundError as e:
            logger.debug(f"No readme found: {e}")

        return ""

    def delete_repository(self, repository: object) -> bool:
        try:
            if isinstance(repository, str):
                repository = self.get_repository_by_name(repository)

            return repository.delete()
        except exceptions.NotFoundError:
            logger.warning("No Repo found")
        return False

    def delete_fork_repository(self, repository) -> bool:
        """
        Deletes fork repository on current user's repo list

        :param repository:
        :return: bool
        """

        _, repo_name = repository.split("/")

        fork_repo_name = f"{self.get_me()}/{repo_name}"

        return self.delete_repository(fork_repo_name)

    def create_fix_typo_pull_request(
        self, typo_readme_repository, modified_readme
    ) -> PullRequest:
        """
        Clone repo and create a PullRequest with typo fix

        :param typo_readme_repository: str
        :param modified_readme: str
        :return: PullRequest
        """
        repo = self.get_repository_by_name(typo_readme_repository)
        sleep(1)
        fork = repo.create_fork()
        sleep(1)

        try:
            ref = fork.ref("heads/{}".format(repo.default_branch))
            fork.create_branch_ref(TYPO_BRANCH_NAME, ref.object.sha)
            sleep(1)

            # commit modified readme
            fork.readme().update(
                TYPO_COMMIT_MESSAGE,
                branch=TYPO_BRANCH_NAME,
                content=modified_readme.encode("utf-8"),
            )
            sleep(1)
            pull_request = repo.create_pull(
                title=TYPO_PULL_REQUEST_TITLE,
                base=repo.default_branch,
                head="{}:{}".format(self.get_me(), TYPO_BRANCH_NAME),
            )

            return pull_request
        except Exception as e:
            logger.exception("Deleting fork")
            fork.delete()

            raise e

    @staticmethod
    def get_repo_link(repository) -> str:
        return f"https://github.com/{repository}"

    @staticmethod
    def get_repo_link_with_context(repository: str, context: str) -> str:
        """
        Build a link to the specific part of the GitHub repository readme page
        see https://support.google.com/chrome/answer/10256233

        :param repository: string
        :param context: string
        :return: string
        """
        return f"https://github.com/{repository}#:~:text={urllib.parse.quote(context)}"
