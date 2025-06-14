import requests
import pandas as pd
from io import BytesIO
#from scraper.utils.excel_reader import get_science_metrix_hierarchy
from scraper.utils.classification_data_reader import get_science_metrix_hierarchy, hierarchy_with_keywords
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import string
import nltk
try:
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords')
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))


class RSDScraper:
    
    stop_words = set(stopwords.words('english'))
    token= os.getenv('GITHUB_TOKEN')
    def __init__(self):
        self.data = None
    @staticmethod
    def fetch_data(API):
        """Fetch data from the Research Software Directory API."""
        response = requests.get(API)
        if response.status_code == 200:
            data = response.json() 
            #print(self.data)
            return data
        else:
            raise Exception(f"Error fetching data: {response.status_code}")

    def to_dataframe(self): # not needed
        """Convert JSON data to Pandas DataFrame."""
        if self.data is None:
            raise Exception("No data to convert. Fetch data first.")
        return pd.DataFrame(self.data)
    @staticmethod
    def clean_text(text):
    # Lowercase
       text = text.lower()

    # Remove punctuation
       text = text.translate(str.maketrans('', '', string.punctuation))

    # Tokenize
       words = re.findall(r'\b\w+\b', text)

    # Remove stopwords
       filtered_words = [word for word in words if word not in stop_words]

    # Return cleaned text as string or list
       return " ".join(filtered_words)

    @staticmethod
    def find_domain(data):
       domain_data = get_science_metrix_hierarchy()
       
       keywords_domain_data= hierarchy_with_keywords(domain_data)
      
       
       
       df = pd.DataFrame(data)  
       all_matches = []
       # Iterate over each description in the DataFrame
       for idx, row in df.iterrows():
         statement = str(row["short_statement"])
         description=str(row["description"])
         cleaned_text = RSDScraper.clean_text(description) # data preprocessing
         readme_words = set(cleaned_text.split())
         brand_name=str(row["brand_name"])
         slug_name=str(row["slug"])
         matches_list = []
         get_started_url=str(row["get_started_url"])
         found_match = False  # Flag if any match is found in the current statement
         if "funded" in description.lower() or "funding" in description.lower():
                  funding = "yes"
         else:
                  funding = "N/A" 
        # Loop through the hierarchy to find a matching subfield
         ''''for domain, fields in domain_data.items():
            for field, subfields in fields.items():
                for subfield in subfields:
                    # Check if the subfield keyword is present in the description (case-insensitive)
                    if subfield.lower() in description.lower():
                        # Save the result as a dictionary
                        matches_list.append({
                            "brand_name" :brand_name,
                            "get_started_url": get_started_url,
                            "slug_name":slug_name,
                            "short_statement": statement,
                            "Domain": domain,
                            "Field": field,
                            "Subfield": subfield
                        })
                        found_match = True
                        break  # Breaks out of subfield loop
                if found_match:
                    break  # Breaks out of field loop
            if found_match:
                break  # Breaks out of domain loop'''
         for domain, fields in keywords_domain_data.items():
            for field, subfields in fields.items():
                for subfield, keywords in subfields.items():
                    if subfield == "__field_keywords__":
                        continue
                    matched_keywords = [kw for kw in keywords if kw in readme_words]
                    score = len(matched_keywords)

                    if score > 1:  # Only keep matches with score > 1
                        matches_list.append({
                            "brand_name" :brand_name,
                            "get_started_url": get_started_url,
                            "slug_name":slug_name,
                            "short_statement": statement,
                            "Domain": domain,
                            "Field": field,
                            "Subfield": subfield,
                            "project_id": row.get("project_id", idx),
                            "matched_keywords": ", ".join(matched_keywords),
                            "score": score
                        })

        # Keep only matches with highest score for this project
         if matches_list:
            max_score = max(m["score"] for m in matches_list)
            top_matches = [m for m in matches_list if m["score"] == max_score]
            all_matches.extend(top_matches)
       
    # Create a DataFrame from the matches list
       df_matches = pd.DataFrame(all_matches)
       
       return df_matches, funding
    
    @staticmethod
    # Function to scrape GitHub link from an RSD software page
    def get_github_from_rsd_page(url):
        try:
          headers = {"User-Agent": "Mozilla/5.0"}
          response = requests.get(url, headers=headers, timeout=10)

          if response.status_code != 200:
            #print(f"Failed to access {url}")
            return None

          soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for GitHub link 
          github_links = [a["href"] for a in soup.find_all("a", href=True) if "github.com" in a["href"]]
        
        # Return the first GitHub link found
          return github_links[0] if github_links else None

        except Exception as e:
           #print(f"Scraping Error for {url}: {e}")
           return None
       
    @staticmethod
    def extract_github_repo_info(github_url):
    # GitHub repo URL format: https://github.com/owner/repo_name
        if not github_url:
           raise ValueError("GitHub URL cannot be None or empty")
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', github_url)
        if match:
            owner = match.group(1)
            repo_name = match.group(2)
            return owner, repo_name
        else:
            raise ValueError("Invalid GitHub repository URL")
    @staticmethod
    # Function to check if selected files exists in the repository
    def check_files_in_repo(github_repo_url):
        if not github_repo_url:
            return {"error": "No GitHub repository URL provided"}

        try:
            repo_owner, repo_name = RSDScraper.extract_github_repo_info(github_repo_url)
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
            headers = {"Accept": "application/vnd.github.v3+json",
                       "Authorization": f"token {RSDScraper.token}"}

            response = requests.get(url, headers=headers)

            # Handle API rate limits and errors
            if response.status_code == 403:
                
                return {"error": "GitHub API rate limit exceeded"}
            elif response.status_code == 404:
                return {"error": "Repository not found"}
            elif response.status_code != 200:
                return {"error": f"GitHub API error: {response.status_code}"}

            try:
                files = response.json()  # Ensure JSON response
            except requests.JSONDecodeError:
                return {"error": "Invalid JSON response from GitHub"}
        
            file_names = [file["name"].lower() for file in files]
          
            # Check for specific files, return only boolean values
            return {
                "README": any(name in ["readme.md", "readme.rst"] for name in file_names),
                "License": any("license" in name for name in file_names),
                "Citation": any("citation" in name for name in file_names),
                "Documentation": any("docs" in name or "documentation" in name for name in file_names),
            }
        except ValueError as e:
            return {"error": str(e)}
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}











    