import aiohttp
import asyncio
import re

from .get_contributors import GetContributors
from .get_readme import GetReadme
from datetime import datetime, timedelta
import os 
import json


class GetDownloads:
      
   
    
    def __init__(self):
        self.data = None

    @staticmethod
    async def get_github_release_downloads(owner, repo, session):
        """Fetch total downloads from GitHub Releases API."""
        url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {os.getenv('GITHUB_TOKEN')}"  
        }
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                releases = await response.json()
                if not releases:
                    return "No releases found for this repository"
                total_downloads = sum(
                    asset["download_count"] for release in releases for asset in release.get("assets", [])
                )
                return total_downloads
            else:
                return f"Error fetching GitHub releases: {response.status}"
    

    @staticmethod
    async def check_readme_for_install(readme_url, github_repo, session):
      try:
        if readme_url:
            # Fetch the README content using the download_url
            async with session.get(readme_url) as readme_content:
                readme_text = await readme_content.text()

                # Check if 'pip install' is mentioned in the README
                if "pip install" in readme_text.lower():
                    return github_repo  # Return GitHub repo name if 'pip install' is found
                elif "npm install" in readme_text.lower() or "npm ci" in readme_text.lower():
                    return github_repo  # Return GitHub repo name if 'npm install' or 'npm ci' is found
                elif "conda install" in readme_text.lower() or "npm ci" in readme_text.lower():
                    return github_repo  # Return GitHub repo name if 'npm install' or 'npm ci' is found
                elif "install.packages" in readme_text.lower() or "npm ci" in readme_text.lower():
                    return github_repo  # Return GitHub repo name if 'npm install' or 'npm ci' is found
              
                else:
                    return "No 'pip install' or 'npm install' or 'conda install' found in README."

        else:
            return {"message": f"Error fetching repository content: No README URL provided."}

      except Exception as e:
        return {"message": f"Error: {e}"}  # Catch any exceptions and return the error message

   
    @staticmethod
    async def get_pypi_downloads(package_name, session):
             """Fetch downloads from PyPI."""
          
             url = f"https://pypistats.org/api/packages/{package_name}/recent"  # Correct API URL
             try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()  # Await the JSON response
                        return {
                            "last_day": data["data"]["last_day"],
                            "last_week": data["data"]["last_week"],
                            "last_month": data["data"]["last_month"]
                        }
                    else:
                        return f"Error fetching PyPI downloads: {response.status}"
             except Exception as e:
                return f"Error: {e}"  # Catch any exceptions and return the error message
    @staticmethod
    async def get_pepy_downloads(package_name, session):
            url = f"https://api.pepy.tech/api/v2/projects/{package_name}"
            headers = {"X-API-Key": os.getenv('api_key')}  
        
            try:
              async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()  # Await the JSON response
                    # Extracting the total downloads
                    total_downloads = data.get("total_downloads", "Total downloads not available")
                    return total_downloads
                else:
                    return f"Error: Unable to fetch data. Status code: {response.status}"
            except Exception as e:
                 return f"Error: {e}"  # Catch any exceptions and return the error message
       
    @staticmethod
    async def get_npm_downloads(package_name, session):
            """Fetch last-week and last-month downloads from npm."""
       
            last_week_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
            last_month_url = f"https://api.npmjs.org/downloads/point/last-month/{package_name}"
        
            try:
               async with session.get(last_week_url) as last_week_resp, session.get(last_month_url) as last_month_resp:
                if last_week_resp.status == 200 and last_month_resp.status == 200:  # Use .status for HTTP response code
                    last_week_data = (await last_week_resp.json()).get("downloads", 0)
                    last_month_data = (await last_month_resp.json()).get("downloads", 0)
                    return {"last_week": last_week_data, "last_month": last_month_data}
                else:
                    return f"Error fetching npm stats: {last_week_resp.status}, {last_month_resp.status}"  # Corrected to .status
            except Exception as e:
               return f"Error: {e}"  # Catch any exceptions and return the error message
       
    @staticmethod
    async def get_downloads_from_zenodo(doi, session):
      """Fetch download statistics from Zenodo using the DOI."""
      download_data = {}

      if doi and isinstance(doi, str):
        # Extract the record ID from DOI (assuming DOI is in the format: https://doi.org/{id})
        zenodo_record_id = doi.split('/')[-1].replace('zenodo.', '')  

        # Construct the Zenodo API URL for the record
        zenodo_api_url = f"https://zenodo.org/api/records/{zenodo_record_id}"
        
        try:
            async with session.get(zenodo_api_url) as zenodo_response:
                if zenodo_response.status == 200:
                    zenodo_data = await zenodo_response.json()

                    # Extract total download stats from the "stats" section
                    stats = zenodo_data.get("stats", {})
                    downloads_total = stats.get("downloads", 0)  # Total downloads
                    unique_downloads = stats.get("unique_downloads", 0)  # Unique downloads
                    views_total = stats.get("views", 0)  # Total views
                    unique_views = stats.get("unique_views", 0)  # Unique views

                    # Add the download stats to the result dictionary
                    download_data['zenodo_downloads_total'] = downloads_total
                    download_data['zenodo_unique_downloads'] = unique_downloads
                    download_data['zenodo_views_total'] = views_total
                    download_data['zenodo_unique_views'] = unique_views
                else:
                    download_data['zenodo_error'] = f"Error fetching Zenodo data: {zenodo_response.status}"
        
        except Exception as e:
            download_data['zenodo_error'] = f"Error during Zenodo request: {str(e)}"
      else:
        download_data['zenodo_error'] = "No DOI found in result."

      return download_data
    @staticmethod
    async def get_docker_stats(docker_image, session):
      if docker_image and isinstance(docker_image, dict):  # Check if docker_image is a dictionary
        url = f"https://hub.docker.com/v2/repositories/{docker_image['username']}/{docker_image['repo']}/"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()  # Use async method for JSON
                    pull_count = data.get('pull_count', 'N/A')
                    star_count = data.get('star_count', 'N/A')
                    return {'pull_count': pull_count, 'star_count': star_count}
                else:
                    return {'pull_count': None, 'star_count': None}
        except Exception as e:
            return {'pull_count': None, 'star_count': None}
      else:
        # In case docker_image is None or not a dictionary
        return {'pull_count': 'N/A', 'star_count': 'N/A'}


    @staticmethod
    async def get_cran_downloads(package_name, start_date, end_date, session):
             """Fetch downloads from PyPI."""
          
             url = f"https://cranlogs.r-pkg.org/downloads/daily/{start_date}:{end_date}/{package_name}"
             try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()  # Await the JSON response
                        if isinstance(data, list):  # CRAN API returns a list
                                downloads = [entry["downloads"] for entry in data]   
                                return downloads
                        else:
                                return f"Unexpected response format: {data}"
                    else:
                        return f"Error fetching cran downloads: {response.status}"
             except Exception as e:
                return f"Error: {e}"  # Catch any exceptions and return the error message
    @staticmethod
    async def get_conda_downloads(channel, package_name,  session):
             """Fetch downloads from conda."""
          
             url = f"https://api.anaconda.org/package/{channel}/{package_name}"
             try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()  # Await the JSON response
                        if "files" in data:
                             total_downloads = sum(file["ndownloads"] for file in data["files"])
       
                        return total_downloads
                        
                    else:
                        return f"Error fetching conda downloads: {response.status}"
             except Exception as e:
                return f"Error: {e}"  # Catch any exceptions and return the error message

    @staticmethod
    async def fetch_data_for_repo(github_owner, github_repo, session):
        """Fetch all data for a specific repository."""
        # Fetch the download counts for GitHub releases
        github_downloads = await GetDownloads.get_github_release_downloads(github_owner, github_repo, session)
        # Check if PyPI package is available
        readme_url= await GetReadme.get_readmefile(github_owner, github_repo, session)
        
        zenodo_url= await GetReadme.check_readme_for_zenodo_badge(readme_url,session)
        package_name = await GetDownloads.check_readme_for_install(readme_url, github_repo, session)
        pypi_downloads = await GetDownloads.get_pypi_downloads(package_name, session)
        npm_downloads= await GetDownloads.get_npm_downloads(package_name, session)
       
        pepy_downloads= await GetDownloads.get_pepy_downloads(package_name, session)
        zenodo_downloads= await GetDownloads.get_downloads_from_zenodo(zenodo_url, session)
        docker_image= await GetReadme.extract_docker_image(readme_url,session)
        
        docker_data = await GetDownloads.get_docker_stats(docker_image, session)
        today = datetime.today()
        start_date = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        cran_data= await GetDownloads.get_cran_downloads(package_name, start_date, end_date, session)
        conda_data= await GetDownloads.get_conda_downloads(github_owner,package_name, session)
        stats_data= await GetReadme.get_github_repo_stats(github_owner,github_repo, session)
        contributors_data, total_contributors= await GetContributors.get_active_contributors(github_owner,github_repo, session)
       
        download_data = {
            "GitHub": github_downloads,
            "PyPI": pypi_downloads,
            "NPM": npm_downloads,
            "Pepy.tech": pepy_downloads,
            "Zenodo": zenodo_downloads,
            "docker": docker_data,
            "cran": cran_data,
            "conda": conda_data,
        }  
        repo_data={ "GITHUB_stats": stats_data,
             "Contributors_data":contributors_data,
             "Contributors_no": total_contributors}    
        
        return  download_data, repo_data

    @staticmethod
    async def get_all_downloads(owner, repo):
        """Fetch download data for a single repository."""
        async with aiohttp.ClientSession() as session:
            download_data, repo_data = await GetDownloads.fetch_data_for_repo(owner, repo, session)
            return download_data, repo_data


