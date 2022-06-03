import re
import logging
from github3 import GitHub
from github3.repos.repo import Repository

logger = logging.getLogger(__name__)


class GithubClient:
    typo_branch_name = 'fix-readme-typo'
    typo_commit_text = 'Fix readme typo'
    typo_pull_request_name = 'Fix readme typo'

    def __init__(self, token: str):
        self.gh = GitHub(token=token)

    def get_most_starred_repos_for_date(self, date):
        return self.gh.search_repositories('created:{0}..{0}'.format(date), order='stars')

    def get_me(self):
        return self.gh.me()

    def get_repository_by_name(self, name: str) -> Repository:
        owner, repository_name = name.split('/')

        return self.gh.repository(owner, repository_name)

    def delete_repository(self, repository) -> bool:
        if isinstance(repository, str):
            repository = self.get_repository_by_name(repository)

        return repository.delete()

    def create_fix_typo_pull_request(self, typo_readme_repository, modified_readme):
        fork = typo_readme_repository.repository.create_fork()

        try:
            ref = fork.ref('heads/{}'.format(typo_readme_repository.repository.default_branch))
            fork.create_branch_ref(self.typo_branch_name, ref.object.sha)

            # commit modified readme
            fork.readme().update(self.typo_commit_text, branch=self.typo_branch_name, content=modified_readme)

            typo_readme_repository.repository.create_pull(
                title=self.typo_pull_request_name,
                base=typo_readme_repository.repository.default_branch,
                head='{}:{}'.format(self.get_me(), self.typo_branch_name)
            )
        except Exception as e:
            fork.delete()
            logger.exception("Deleting fork")

            raise e
