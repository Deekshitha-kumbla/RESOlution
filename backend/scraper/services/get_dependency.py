
import os
import requests
from dotenv import load_dotenv
from datetime import datetime


class GetDependency:
    
    token= os.getenv('GITHUB_TOKEN')
    def __init__(self):
        self.data = None

    @staticmethod
    def get_repositories_using_package(github_repo):
      headers = {
        'Authorization': f'token {GetDependency.token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
      total_found = 0
      seen_repos = set()  # Avoid double-counting
      page = 1

      while True:
        # Search for all relevant files using 'OR' operator
        search_url = f'https://api.github.com/search/code?q={github_repo}+in:file+filename:requirements.txt+OR+filename:setup.py+OR+filename:pyproject.toml+OR+filename:Pipfile+OR+filename:Pipfile.lock+OR+filename:environment.yml+OR+filename:tox.ini+OR+filename:Dockerfile+OR+filename:.github/workflows/*.yml+OR+filename:README.md&per_page=30&page={page}'
        
        response = requests.get(search_url, headers=headers)
        
        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"

        data = response.json()
        items = data.get("items", [])
        
        if not items:
            break

        for item in items:
            repo_data = item["repository"]
            repo_full_name = repo_data["full_name"]

            # Skip already counted repos
            if repo_full_name in seen_repos:
                continue

            # Fetch full repo details
            repo_url = repo_data["url"]
            repo_response = requests.get(repo_url, headers=headers)

            if repo_response.status_code != 200:
                continue

            repo_info = repo_response.json()
            created_str = repo_info.get("created_at")
            
            if not created_str:
                continue

            created_date = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%SZ")
            total_found += 1
            seen_repos.add(repo_full_name)

        # If fewer than 30 items are returned, break the loop
        if len(items) < 30:
            break

        page += 1

      return total_found