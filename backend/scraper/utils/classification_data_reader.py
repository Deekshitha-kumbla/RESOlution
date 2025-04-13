import pandas as pd
import os
from collections import defaultdict
import re

def read_excel_data():
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "erc_classification.xlsx")
    
    # Read Excel file
    df = pd.read_excel(file_path, header=None, engine="openpyxl")
    df = df.dropna()
    
    # Assign first row as column headers
    df.columns = df.iloc[0]
    df = df[0:].reset_index(drop=True)
    
    return df
def slugify(text):
    return str(text).replace("\xa0", " ").strip()

# Apply cleaning to all relevant columns
def clean_dataframe(data):
    for col in data.columns:
        data[col] = data[col].apply(slugify)
    return data
def extract_keywords(text):
    # Extract key terms from label 
    tokens = re.findall(r'\b\w+\b', text.lower())
    
    stopwords = { "and", "of"} # may be add more later
    return [t for t in tokens if t not in stopwords]

def get_science_metrix_hierarchy():
    data = read_excel_data()  
    #data= clean_dataframe(data)
    required_columns = {"Main fields", "Long label", "Short label"}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"Missing required columns: {required_columns - set((data.columns))}")

    science_metrix_hierarchy = defaultdict(lambda: defaultdict(list))
    for _, row in data.iterrows():
        domain = row["Main fields"]
        field = row["Long label"]
        subfield = row["Short label"]


        science_metrix_hierarchy[domain][field].append(subfield)

# Convert to normal dict
    science_metrix_hierarchy = {
    d: {
        f: s for f, s in fields.items()
    } for d, fields in science_metrix_hierarchy.items()
}   
    
    return science_metrix_hierarchy

    ''''# Populate the hierarchical dictionary
    for _, row in data.iterrows():
        domain = row["Main fields"]
        field = row["Long label"]
        subfield = row["Short label"]
        science_metrix_hierarchy[domain][field].append(subfield)
        
    '''

    # Convert defaultdict to normal dict
    #return {k: dict(v) for k, v in science_metrix_hierarchy.items()}

def hierarchy_with_keywords(metrix_hierarchy):
    keyword_hierarchy = defaultdict(lambda: defaultdict(dict))
    #print(metrix_hierarchy)
    for domain, fields in metrix_hierarchy.items():
      for field, subfields in fields.items():
        field_keywords = extract_keywords(field)
        
        keyword_hierarchy[domain][field]["__field_keywords__"] = field_keywords

        for subfield in subfields:
            subfield_keywords = extract_keywords(subfield)
            keyword_hierarchy[domain][field][subfield] = subfield_keywords
            
    return keyword_hierarchy  
    
