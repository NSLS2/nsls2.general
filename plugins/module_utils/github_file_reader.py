"""Utility module for reading contents of files from a GitHub repository."""

import base64

import requests


class GitHubFileReader:
    """Read files from GitHub and return dictonary"""

    def __init__(self, owner, repo, token=None):
        self._owner = owner
        self._repo = repo

        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/vnd.github+json"})
        self._session.headers.update({"X-GitHub-Api-Version": "2022-11-28"})

        if token is not None:
            self._session.headers.update({"Authorization": f"Bearer {token}"})

        self._contents = []

    def get_tree(self, branch, path=None, recursive=None):
        """Get tree from GitHub API"""
        sha = self._get_branch_sha(branch)
        files = self._get_tree(sha, path=path, recursive=recursive)
        for file in files:
            if file["type"] == "blob":
                blob = self._get_blob(file["url"])
                self._process_file(blob, file["path"])

        return self._contents

    def _get_json(self, url):
        r = self._session.get(url)
        r.raise_for_status()
        j = r.json()
        return j

    def _get_branch_sha(self, branch):
        # Get from here
        j = self._get_json(
            f"https://api.github.com/repos/{self._owner}/"
            f"{self._repo}/branches/{branch}"
        )
        head_tree_sha = j["commit"]["commit"]["tree"]["sha"]
        return head_tree_sha

    def _get_tree(self, sha, path=None, recursive=None):
        _recursive = bool(recursive)
        j = self._get_json(
            f"https://api.github.com/repos/{self._owner}/{self._repo}/"
            f"git/trees/{sha}?recursive=f{_recursive}"
        )

        if path is not None:
            # We now select only part of the path
            files = [leaf for leaf in j["tree"] if leaf["path"].startswith(path)]
        else:
            files = j["tree"]

        return files

    def _get_blob(self, blob_url):
        j = self._get_json(blob_url)
        return j

    def _process_file(self, j, name=None):
        """Process json contents of a GitHub file"""
        # if we have content, then we can process
        if "content" in j:
            if j["encoding"] == "base64":
                _content = base64.b64decode(j["content"])
            else:
                raise RuntimeError("Invalid encoding")

            if name is None:
                if "name" in j:
                    name = j["name"]
                else:
                    name = ""

            self._contents.append({"content": _content, "name": name})

    def get_content(self):
        """Return content dictonary"""
        return self._contents
