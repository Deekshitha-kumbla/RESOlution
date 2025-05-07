import aiohttp
import asyncio
import re
import os
import requests
from dotenv import load_dotenv
import time


class GetUserEngagement:
    
    token= os.getenv('GITHUB_TOKEN')
    HEADERS = {
    "Authorization": f"token {token}",  
    "Accept": "application/vnd.github+json"
}
    def __init__(self):
        self.data = None
    
    @staticmethod
    def get_reviews(review_url):
      """Helper function to get reviews for a pull request."""
      response = requests.get(review_url, headers=GetUserEngagement.HEADERS)
      if response.status_code == 200:
        reviews = response.json()
        return reviews
      elif response.status_code == 403:
        time.sleep(60)
        return GetUserEngagement.get_reviews(review_url)  # Recursion if rate limit is hit
      else:
        #print(f"Error fetching reviews: {response.status_code}")
        return f"Error fetching reviews: {response.status_code}"
    @staticmethod
    def get_code_reviews(github_owner, github_repo):
      """Get code reviews from the GitHub API."""
      url = f"https://api.github.com/repos/{github_owner}/{github_repo}/pulls?state=all"
      total_reviews = 0
      page = 1

      while True:
        response = requests.get(f"{url}&page={page}", headers=GetUserEngagement.HEADERS)
        if response.status_code == 200:
            data = response.json()
            
            if not data:  # Exit the loop if there are no more pull requests
                break
            for pr in data:
                pr_number = pr['number']
                review_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/pulls/{pr_number}/reviews"
                
                reviews = GetUserEngagement.get_reviews(review_url)
                
                total_reviews += len(reviews)
            page += 1  # Move to the next page
        elif response.status_code == 403:
            time.sleep(60)
            continue  # Retry if rate limit is hit
        else:
            return f"Error fetching pull requests: {response.status_code}"
            break

      return total_reviews
    @staticmethod
    def get_discussion_statistics(github_owner,github_repo):
        query = """
        {
  repository(owner: "%s", name: "%s") {
    discussions(first: 100) {
      nodes {
        title
        author {
          login
        }
        comments(first: 100) {
          nodes {
            author {
              login
            }
          }
        }
      }
    }
  }
}
         """ % (github_owner, github_repo)

        response = requests.post("https://api.github.com/graphql", json={'query': query}, headers=GetUserEngagement.HEADERS)

        if response.status_code == 200:
          data = response.json()
          if (
        'data' in data and 
        data['data'].get('repository') and 
        'discussions' in data['data']['repository']
    ):
           discussions = data['data']['repository']['discussions']['nodes']

           total_discussions = len(discussions)
           total_comments = 0
           unique_users = set()

           for discussion in discussions:
              author = discussion.get("author", {}).get("login")
              if author:
                 unique_users.add(author)
                 comments = discussion.get("comments", {}).get("nodes", [])
                 total_comments += len(comments)
                 for comment in comments:
                   comment_author = comment.get("author", {}).get("login")
                   if comment_author:
                       unique_users.add(comment_author)
                       return {"total_discussions": total_discussions, 
                               "total_comments": total_comments,
                               "unique_users": len(unique_users)}
          

   

                   else:
                      return f"Query failed: {response.status_code}, {response.text}"
         
          
    @staticmethod
    def get_issue_engagement_stats(github_owner, github_repo):
        headers = {
        'Authorization': f'token {GetUserEngagement.token}',
        'Accept': 'application/vnd.github.squirrel-girl-preview+json'  # Needed for reactions
        }

        total_comments = 0
        reaction_counts = {
        '+1': 0, '-1': 0, 'laugh': 0, 'hooray': 0,
        'confused': 0, 'heart': 0, 'rocket': 0, 'eyes': 0
        }

    # === Get issue comments (excluding bots) ===
        comments_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/issues/comments?per_page=100"
        page = 1
        while True:
            response = requests.get(f"{comments_url}&page={page}", headers=headers)
            if response.status_code == 403:
                
                time.sleep(60)
                continue
            elif response.status_code != 200:
                 return f"Error fetching comments: {response.status_code} - {response.text}"

            comments = response.json()
            
            if not comments:
                break

            for comment in comments:
               user = comment.get("user", {})
               if user.get("type") != "Bot":
                total_comments += 1
            page += 1

          # === Get issue reactions ===
        issues_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/issues?state=all&per_page=100"
        page = 1
        while True:
            response = requests.get(f"{issues_url}&page={page}", headers=headers)
            if response.status_code == 403:
             
              time.sleep(60)
              continue
            elif response.status_code != 200:
               return f"Error fetching issues: {response.status_code} - {response.text}"

            issues = response.json()
            if not issues:
               break

            for issue in issues:
              issue_number = issue['number']
              reactions_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/issues/{issue_number}/reactions"
              reactions_response = requests.get(reactions_url, headers=headers)
              if reactions_response.status_code == 200:
                reactions = reactions_response.json()
                
                for reaction in reactions:
                    reaction_type = reaction.get('content')
                    if reaction_type in reaction_counts:
                        reaction_counts[reaction_type] += 1
            page += 1

        total_reactions = sum(reaction_counts.values())

        return {
        'total_comments': total_comments,
        'total_reactions': total_reactions,
        'reaction_breakdown': reaction_counts
    }
