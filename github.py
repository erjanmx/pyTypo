import requests


class GitHub(object):
    base_url = 'https://api.github.com/'

    def __init__(self, token, client=None):
        if client is None:
            client = requests

        self.token = token
        self.client = client

    def _request(self, url, method='get', params=(), data=(), headers=()):
        url = self.base_url + url
        _headers = dict(headers)
        _headers['Authorization'] = 'token %s' % self.token

        return self.client.request(url=url, method=method, headers=_headers, params=params, data=data)

    def get_readme_content(self, username_repo):
        response = self._request(url='repos/%s/readme' % username_repo, headers={
            'Accept': 'application/vnd.github.V3.raw'
        })

        return str(response.content)

    def get_popular_repos_for_date(self, date):
        response = self._request(url='search/repositories', params={
            'q': 'created:{0}..{0}'.format(date),
            'sort': 'stars',
            'order': 'desc',
        })

        json = response.json()

        return list(map(lambda repo: repo['full_name'], json['items']))
