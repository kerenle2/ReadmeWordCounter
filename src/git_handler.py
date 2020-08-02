import requests
import base64
import logging

GIT_API_REPOS_URL = "https://api.github.com/repos/"
GIT_API_HEADERS = {"accept": "application/vnd.github.v3+json"}


class GitHandler:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def extract_readme_content(self):
        """
        extract the readme content from given url using GIT REST API.
        """
        full_url = GIT_API_REPOS_URL + self.repo_path + "/readme"
        try:
            res = requests.get(full_url, headers=GIT_API_HEADERS)
            encoded_content = res.json()["content"]
            decoded_content = base64.b64decode(encoded_content).decode()
            logging.info("readme content extracted successfully")
            return decoded_content
        except Exception:
            logging.error("the repo {} has nor readme file".format(self.repo_path))
            return None



