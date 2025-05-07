
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from django.http import JsonResponse
from pyvis.network import Network
from django.http import HttpResponse

class GetDomainNetworkgraph:
    
    
    def __init__(self):
        self.data = None

    @staticmethod
    def get_networkgraph(domain_matches):
    # Group by counts
     domain_counts = domain_matches.groupby("Domain")["project_id"].nunique().reset_index()
     subfield_counts = domain_matches.groupby("Subfield")["project_id"].nunique().reset_index()
     field_counts = domain_matches.groupby("Field")["project_id"].nunique().reset_index()

     domain_color = "#FF7F7F"  # coral
     field_color = "#87CEFA"   # light sky blue
     subfield_color = "#EE82EE" # violet

    # Create network
     net = Network(height="800px", width="100%", notebook=True, directed=True, cdn_resources='in_line')
     net.force_atlas_2based()

     added_nodes = set()

    # Add domain nodes
     for _, row in domain_counts.iterrows():
        domain_str = str(row["Domain"])
        project_count = row["project_id"]
        if domain_str not in added_nodes:
            net.add_node(domain_str, label=domain_str, size=int(10 + project_count), color=domain_color, title=f"{project_count} projects")
            added_nodes.add(domain_str)
 
    # Add field and subfield nodes
     for _, row in domain_matches.iterrows():
        dom = str(row["Domain"])
        field = str(row["Field"])
        sub = str(row["Subfield"])

        # Add field node
        if field and field not in added_nodes:
            project_count = field_counts[field_counts["Field"] == field]["project_id"].values[0]
            net.add_node(field, label=field, size=int(10 + project_count), color=field_color, title=f"{project_count} projects")
            net.add_edge(dom, field)
            added_nodes.add(field)

        # Add subfield node
        if sub and sub not in added_nodes:
            project_count = subfield_counts[subfield_counts["Subfield"] == sub]["project_id"].values[0]
            net.add_node(sub, label=sub, size=int(10 + project_count), color=subfield_color, title=f"{project_count} projects")
            net.add_edge(field, sub)
            added_nodes.add(sub)
     html = net.generate_html()
     response = HttpResponse(html)
     response["X-Frame-Options"] = "ALLOWALL"
    
    # Extract the network data (nodes and edges)
     #net_data = net.get_network_data()

    # Return the network data (nodes and edges) which are serializable in JSON format
     #return net.show("domain_network_graph.html")
     return response