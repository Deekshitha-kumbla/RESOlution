from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from .services.get_dependency import GetDependency
from .services.get_readme import GetReadme
from .services.get_downloads import GetDownloads
from .services.rsd_scraper import RSDScraper
from .services.get_citationdata import GetCitation
import pandas as pd
import os

class RSDDataView(View):
    @method_decorator(csrf_exempt)
    def get(self, request):
        domain_filter = request.GET.get("domain", "").strip().lower().replace('\xa0', ' ')
        subdomain_filter = request.GET.get("subdomain", "").strip().lower().replace('\xa0', ' ')
        subfield_filter = request.GET.get("subfield", "").strip().lower().replace('\xa0', ' ')

       
        scraper = RSDScraper()
        downloads=GetDownloads()
        citation=GetCitation()
        RSD_API= os.getenv('RSD_API')
        helmoltz_API=os.getenv('helmholtz.software_API')
        
        data= scraper.fetch_data(RSD_API)
        
        #data_helmoltz=scraper.fetch_data(helmoltz_API)
        #data = pd.concat([data_rsd, data_helmoltz.iloc[1:]], ignore_index=True)
        #data = data_rsd + data_helmoltz[1:]
        #print(len(data))
        domain_results, funding = scraper.find_domain(data)
        domain_results= domain_results.drop_duplicates()
        
        # Check if 'slug_name' contains valid data
        if domain_results['slug_name'].isnull().all():
            
            return JsonResponse({"error": "No matching domain found"}, status=404)

        updated_records = []
        errors = []
        print(domain_results)
        domain_results["Domain"] = domain_results["Domain"].str.strip().str.lower()
        domain_results["Field"] = domain_results["Field"].str.strip().str.lower()
        domain_results["Subfield"] = domain_results["Subfield"].str.strip().str.lower()

        
        # Proceed with filtering the domain results based on the filters
        if not domain_results.empty:
           filtered_results = domain_results[
            (domain_results["Domain"].str.match(domain_filter, case=False, na=False)) &
            (domain_results["Field"].str.match(subdomain_filter, case=False, na=False)) &
            (domain_results["Subfield"].str.match(subfield_filter, case=False, na=False))
        ]
           
        else:
        # If domain_results is empty, return the original domain_results
          filtered_results = domain_results
        #print(filtered_results)  
        # Loop through each row in the filtered results
        for record in filtered_results.to_dict(orient="records"):
            slug_name = record.get('slug_name')
           
            short_statement=record.get('short_statement')
            
            if pd.isna(slug_name):  # Skip if slug_name is NaN
                continue

            # Construct the software page URL
            software_page = f"https://research-software-directory.org/software/{slug_name}"

            # Get GitHub repo link from the software page
            github_repo = RSDScraper.get_github_from_rsd_page(software_page)
            print(github_repo)
            if not github_repo:
                errors.append({"slug_name": slug_name, "error": "No GitHub URL found"})
                continue

            try:
                github_owner, github_reponame=RSDScraper.extract_github_repo_info(github_repo)
                downloads_data, repo_data=async_to_sync(downloads.get_all_downloads)(github_owner,github_reponame)
                
                file_presence = scraper.check_files_in_repo(github_repo)
                print(file_presence)
                openalex_id=citation.find_matches(github_repo, short_statement)
                citation_count = citation.get_citation_count(openalex_id)
                dependency_count=GetDependency.get_repositories_using_package(github_repo)
                
                # Add GitHub repo, file presence, other data to the record
                record["github_repo"] = github_repo
                record["file_presence"] = file_presence
                record["downloads"] = downloads_data
                record["citation_count"]=citation_count
                record["repo_data"]=repo_data
                record["dependency_count"]=dependency_count
                record["funding"] =funding
                
                
                # Append the updated record to the results list
                updated_records.append(record)
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)
            # If no GitHub repo found, skip this record
           
        #print((updated_records))
           
        if errors:
           return JsonResponse({"errors": errors}, status=400)   

        # Return the collected results as a JSON response
        return JsonResponse({"matched_records": updated_records}, safe=False)
