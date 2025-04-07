import pandas as pd
import os
from collections import defaultdict

def read_excel_data():
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "sm_journal_classification.xlsx")
    
    # Read Excel file
    df = pd.read_excel(file_path, sheet_name="Pivot-Table_Classification", header=None, engine="openpyxl")
    df = df.dropna()
    
    # Assign first row as column headers
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    
    return df

def get_science_metrix_hierarchy():
    data = read_excel_data()  

    required_columns = {"Domain_English", "Field_English", "SubField_English"}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"Missing required columns: {required_columns - set(data.columns)}")

    science_metrix_hierarchy = defaultdict(lambda: defaultdict(list))

    # Populate the hierarchical dictionary
    for _, row in data.iterrows():
        domain = row["Domain_English"]
        field = row["Field_English"]
        subfield = row["SubField_English"]
        science_metrix_hierarchy[domain][field].append(subfield)

    # Convert defaultdict to normal dict
    return {k: dict(v) for k, v in science_metrix_hierarchy.items()}
