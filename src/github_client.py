import logging

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

    def get_me(self):
        return self.gh.me()

    def get_repository_by_name(self, name: str) -> Repository:
        owner, repository_name = name.replace("https://github.com/", "").split("/")

        return self.gh.repository(owner, repository_name)

    def get_repository_readme(self, repository) -> str:
        try:
            if isinstance(repository, str):
                repository = self.get_repository_by_name(repository)

            return repository.readme().decoded.decode("utf-8")
        except exceptions.NotFoundError:
            logger.warning("No readme found")

        return ""

    def delete_repository(self, repository) -> bool:
        try:
            if isinstance(repository, str):
                repository = self.get_repository_by_name(repository)

            return repository.delete()
        except exceptions.NotFoundError:
            logger.warning("No Repo found")
        return False

    def create_fix_typo_pull_request(
        self, typo_readme_repository, modified_readme
    ) -> PullRequest:
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
        return f"https://github.com/{repository}"
