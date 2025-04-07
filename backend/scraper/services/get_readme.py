import aiohttp
import asyncio
import re
import os


class GetReadme:
    
    
    def __init__(self):
        self.data = None

    @staticmethod
    async def get_readmefile(github_owner, github_repo, session):
        """Check if README mentions pip install or check for package name."""
        url = f"https://api.github.com/repos/{github_owner}/{github_repo}/contents"
        headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}"  # Include GitHub token for authentication
         }
        result = {}

        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    file_info = await response.json()
                    readme_url = None
                    for file in file_info:
                       if file['name'].lower() in ['readme.md', 'readme.rst']:  # Check for both files
                          readme_url = file['download_url']
                          return readme_url
        except Exception as e:
            return {"message": f"Error: {e}"}  # Catch any exceptions and return the error message

    
    @staticmethod
    async def check_readme_for_zenodo_badge(readme_url, session):
        """Fetch the README and check for a Zenodo DOI badge."""
        zenodo_doi = None
    
        try:
          if readme_url:
            # Fetch the README content using the readme_url
            async with session.get(readme_url) as readme_content:
                readme_text = await readme_content.text()

                # Search for Zenodo DOI badge (pattern can be adjusted if necessary)
                badge_pattern = r"https://doi.org/([^ )]+)"  # This regex matches the DOI after the badge URL
                match = re.search(badge_pattern, readme_text)
                
                if match:
                    zenodo_doi = match.group(1)  # Extract the DOI from the matched URL
                    return zenodo_doi
                else:
                    return {"message": "No Zenodo badge found in the README."}
          else:
            return {"message": "No README URL provided."}
        
        except Exception as e:
           return {"message": f"Error fetching README or extracting DOI: {str(e)}"}


    @staticmethod
    async def extract_docker_image(readme_url, session):
        """Fetch README content from a URL and extract Docker image names."""
        try:
            async with session.get(readme_url) as response:
                if response.status != 200:
                    return f"Error: Unable to fetch README (HTTP {response.status})"
                
                readme_content = await response.text()

                # Regex to match Docker image names in docker pull/run commands
                pattern = r"(?:docker\s+(?:pull|run)\s+)(?:-[^\s]+\s+)*([\w\-/:\.]+)"
                matches = re.findall(pattern, readme_content)
                if matches:
                   docker_images = []
                   for match in matches:
                    # Split the Docker image into username and repository
                       if '/' in match:
                        username, repo = match.split('/', 1)
                        docker_images.append((username, repo))  # Return as tuple (username, repo)
                   return docker_images if docker_images else None
                else:
                    return None
        except Exception as e:
            return f"Exception occurred: {str(e)}"

