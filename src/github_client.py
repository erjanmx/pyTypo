import logging
import urllib.parse

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
        """
        Initialize the GitHub client.

        :param token: str, the GitHub access token.
        """
        self.gh = GitHub(token=token)

    def get_most_starred_repos_for_date(self, date):
        """
        Get the most starred repositories for a specific date.

        :param date: The date in the format 'YYYY-MM-DD'.
        :return: The search result of repositories.
        """
        return self.gh.search_repositories(
            "created:{0}..{0}".format(date), order="stars"
        )

    def get_my_public_repositories(self):
        """
        Get the public repositories of the authenticated user.

        :return: The public repositories.
        """
        return self.gh.repositories(type="public")

    def get_me(self) -> str:
        """
        Get the username of the authenticated user.

        :return: The username.
        """
        return self.gh.me()

    def get_repository_by_name(self, name: str) -> Repository:
        """
        Get a repository by its name.

        :param name: The name of the repository in the format 'owner/repository'.
        :return: The repository object.
        """
        owner, repository_name = name.replace("https://github.com/", "").split("/")

        return self.gh.repository(owner, repository_name)

    def get_repository_readme(self, repository: object) -> str:
        """
        Get the readme content of a repository.

        :param repository: The repository object or the name of the repository in the format 'owner/repository'.
        :return: The content of the readme.
        """
        try:
            if isinstance(repository, str):
                repository = self.get_repository_by_name(repository)

            return repository.readme().decoded.decode("utf-8")
        except exceptions.NotFoundError as e:
            logger.debug(f"No readme found: {e}")

        return ""

    def delete_repository(self, repository: object) -> bool:
        """
        Delete a repository.

        :param repository: The repository object or the name of the repository in the format 'owner/repository'.
        :return: True if the repository is deleted successfully, False otherwise.
        """
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

        :param repository: The name of the repository in the format 'owner/repository'.
        :return: True if the fork repository is deleted successfully, False otherwise.
        """
        _, repo_name = repository.split("/")

        fork_repo_name = f"{self.get_me()}/{repo_name}"

        return self.delete_repository(fork_repo_name)

    def create_fix_typo_pull_request(
        self, typo_readme_repository, modified_readme
    ) -> PullRequest:
        """
        Clone repo and create a PullRequest with typo fix

        :param typo_readme_repository: The name of the repository in the format 'owner/repository'.
        :param modified_readme: The modified readme content.
        :return: The created PullRequest object.
        """
        repo = self.get_repository_by_name(typo_readme_repository)

        fork = repo.create_fork()

        try:
            ref = fork.ref("heads/{}".format(repo.default_branch))
            fork.create_branch_ref(TYPO_BRANCH_NAME, ref.object.sha)

            # commit modified readme
            fork.readme().update(
                TYPO_COMMIT_MESSAGE,
                branch=TYPO_BRANCH_NAME,
                content=modified_readme.encode("utf-8"),
            )

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
        """
        Get the link to a GitHub repository.

        :param repository: The name of the repository in the format 'owner/repository'.
        :return: The link to the repository.
        """
        return f"https://github.com/{repository}"

    @staticmethod
    def get_repo_link_with_context(repository: str, context: str) -> str:
        """
        Build a link to the specific part of the GitHub repository readme page.

        :param repository: The name of the repository in the format 'owner/repository'.
        :param context: The context to be highlighted in the link.
        :return: The link to the repository with the specified context.
        """
        return f"https://github.com/{repository}#:~:text={urllib.parse.quote(context)}"
