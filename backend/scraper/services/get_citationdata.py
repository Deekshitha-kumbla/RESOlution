import requests
import re
from datetime import datetime

class GetCitation:
     
    def __init__(self):
        self.data = None
    @staticmethod
    def get_openalex_id(software_name, max_retries=3):
           base_url = "https://api.openalex.org/works"
           
           params = {
              "search": software_name,  # Searching for software name
              #"per_page": 5  
               } # also you can add header including app name , or emial id
           for attempt in range(max_retries):
            response = requests.get(base_url, params=params)
        
            if response.status_code == 200:
             data = response.json()
             results = data.get("results", [])
             if not results:
                return f"No OpenAlex ID found for {software_name}"
             ids = {work.get("title", "Unknown Title"): work.get("id") for work in results}
             return ids
            elif response.status_code == 503:
               return (f"Attempt {attempt + 1}: Server unavailable, retrying...")
               time.sleep(2)  # Wait 2 seconds before retrying
            else:
               return f"Error fetching data: {response.status_code}"
    
           return "Failed after retries due to server error."
           

    @staticmethod
    def find_matches(github_repo, short_statement):
        # Safely get 'short_statement' from domain_results
        

        if not short_statement:  # Check if it's None or empty
            return "Short statement not found"

        # Get OpenAlex IDs
        ids = GetCitation.get_openalex_id(github_repo)

        if not isinstance(ids, dict):  # Ensure ids is a dictionary
            return "Invalid IDs returned"

        # Convert short_statement to lowercase and split into words
        short_statement_words = set(str(short_statement).lower().split())

        for title, doi_id in ids.items():
            # Convert title to lowercase and split into words
            title_words = set(title.lower().split())

            # Check if any word in short_statement matches words in the title
            if short_statement_words & title_words:
                return doi_id.split('/')[-1]  # Extract DOI part

        return "No match found"

    @staticmethod
    def is_valid_openalex_id(openalex_id):
         """Check if the OpenAlex ID is valid (starts with 'W' followed by digits)."""
         return bool(re.match(r"^W\d+$", openalex_id))  # Example: W2955573656
  
    @staticmethod
    def get_citation_count(openalex_id):
          if not GetCitation.is_valid_openalex_id(openalex_id):  # Check if ID is invalid
                return "Invalid OpenAlex ID provided."
          openalex_url = f"https://api.openalex.org/works/{openalex_id}"

          try:
            response = requests.get(openalex_url)

            if response.status_code == 200:
                data = response.json()
                citation_count = data.get("cited_by_count", 0)
                counts_by_year = data.get("counts_by_year", [])
                current_year = datetime.now().year
                last_5_years = {year["year"]: year["cited_by_count"] for year in counts_by_year if year["year"] >= current_year - 5}

                return {
            'Total Citations': citation_count,
            'Citations by Year': last_5_years
            }
            else:
                return f"Error fetching data: {response.status_code}"

          except requests.RequestException as e:
            return f"Request failed: {e}"
        
        