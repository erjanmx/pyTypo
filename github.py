import base64
import requests


class GitHub(object):
    base_url = 'https://api.github.com/'

    def __init__(self, token, client=None):
        if client is None:
            client = requests

        self.token = token
        self.client = client

    def _request(self, url, method='get', params=(), data=(), json=None, headers=()):
        url = self.base_url + url
        _headers = dict(headers)
        _headers['Authorization'] = 'token %s' % self.token

        print(url)
        print(json)

        return self.client.request(url=url, method=method, headers=_headers, params=params, data=data, json=json)

    # def get_readme_content(self, full_name):
    #     response = self._request(url='repos/%s/readme' % full_name, headers={
    #         'Accept': 'application/vnd.github.V3.raw'
    #     })
    #
    #     return str(response.content)

    def get_readme(self, full_name):
        response = self._request(url='repos/%s/readme' % full_name)

        return response.json()

    def get_popular_repos_for_date(self, date):
        response = self._request(url='search/repositories', params={
            'q': 'created:{0}..{0}'.format(date),
            'sort': 'stars',
            'order': 'desc',
        })

        json = response.json()

        return list(map(lambda repo: repo['full_name'], json['items']))

    def fork_repo(self, full_name):
        return self._request(url='repos/%s/forks' % full_name, method='post')

    def create_branch(self, full_name, branch):
        # get master branch info
        master = self._request(url='repos/%s/git/refs/heads/%s' % (full_name, 'master')).json()

        return self._request(url='repos/%s/git/refs' % full_name, method='post', json={
            'ref': 'refs/heads/%s' % branch,
            'sha': master['object']['sha']
        })

    def update_file(self, full_name, content):
        path = 'README.md'
        content = content.encode('utf-8')

        branch = 'fix-readme-typo'

        self.create_branch(full_name, branch)

        response = self._request(url='repos/%s/contents/%s' % (full_name, path), method='put', json={
            'path': path,
            'message': 'Fix typo',
            'branch': branch,
            'sha': self.get_readme(full_name)['sha'],
            'content': str(base64.b64encode(content))[2:-1],
        })

        return response

    def delete_repo(self, full_name):
        pass
