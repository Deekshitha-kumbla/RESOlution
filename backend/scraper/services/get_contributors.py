import os
import aiohttp
from dotenv import load_dotenv

class GetContributors:
    @staticmethod
    async def get_active_contributors(owner, repo, session):
       load_dotenv()
       token = os.getenv('GITHUB_TOKEN')
       url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
       headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
        }

       async with session.get(url, headers=headers) as response:
        if response.status == 200:  # Correct status check
            contributors = await response.json()  # Use await to get the JSON
            contributor_data = []
            total_contributors = len(contributors) 
            contributor_data = [
            {'contributors_username': contributor['login'], 'contributions': contributor['contributions']}
                 for contributor in contributors
                  ]
            return contributor_data, total_contributors  # This is a list of dictionaries with just the necessary information

        
        else:
              return {"error": f"Error fetching data: {response.status}", "detail": await response.text()}
              
      
