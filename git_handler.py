import requests
import base64
import logging

GIT_API_REPOS_URL = "https://api.github.com/repos"

class GitHandler:
    def __init__(self, url):
        self.url = url

    def extract_readme_content(self):
        # url = "https://api.github.com/repos/octocat/hello-world"
        repo_path = self.extract_repo_path()
        full_url = GIT_API_REPOS_URL + repo_path + "/readme"
        headers = {"accept": "application/vnd.github.v3+json"}
        try:
            res = requests.get(full_url, headers=headers)
            encoded_content = res.json()["content"]
            decoded_content = base64.b64decode(encoded_content).decode()
            logging.info("readme content extracted successfully")
            return decoded_content
        except Exception:
            logging.info("there is no readme for repo {}".format(self.url))
            return None

    def extract_repo_path(self):
        path = self.url.split(".com")[1]
        return path

if __name__ == '__main__':
    git = GitHandler("https://api.github.com/repos/octocat/hello-world")
    print(git.extract_readme_content())
