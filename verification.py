import pandas as pd
from rdflib import OWL, RDF, Graph

# Retrives the entities from OWL file 
def retrieve_entities_from_owl(file_path):
    g = Graph()
    g.parse(file_path)
    individuals = set(g.subjects(predicate=RDF.type, object=OWL.NamedIndividual))
    return individuals, g


# Nodes
print("\n")
print("Verifying Nodes")


# Get sub elements for an individual/node
def get_sub_elements(individual, graph):
    sub_elements = {}
    for sub, pred, obj in graph.triples((individual, None, None)):
        if str(obj) != "http://www.w3.org/2002/07/owl#NamedIndividual":
            if str(pred) in sub_elements:            
                if isinstance(sub_elements[str(pred)], list):
                    sub_elements[str(pred)].append(str(obj))
                else:                    
                    sub_elements[str(pred)] = [sub_elements[str(pred)]] + [str(obj)]
            else:
                sub_elements[str(pred)] = [str(obj)]
    
    return sub_elements

# Retrieves abstract nodes from the Asbtract OWL file
def get_abstract_nodes():
  individuals, graph = retrieve_entities_from_owl('Abstract/Abstract-MLOps.owl')
  abstract_nodes = []

  for individual in individuals:
    sub_elements = get_sub_elements(individual, graph)
    
    if f'http://www.example.com/ontologies/abstract-mlops#belongsTo' in sub_elements:      
      if isinstance(sub_elements[f'http://www.example.com/ontologies/abstract-mlops#belongsTo'], list):        
        for value in sub_elements[f'http://www.example.com/ontologies/abstract-mlops#belongsTo']:
          if value == f'http://www.example.com/ontologies/abstract-mlops#Abstract':
            abstract_node = individual
            abstract_nodes.append(abstract_node)
            break  
      else:        
        if sub_elements[f'http://www.example.com/ontologies/abstract-mlops#belongsTo'] == f'http://www.example.com/ontologies/abstract-mlops#Abstract':
          abstract_node = individual
          abstract_nodes.append(abstract_node)

  return abstract_nodes

# Retrieves platform-specific nodes from the respective OWL file
def get_platform_nodes(file_path, platform):
  individuals, graph = retrieve_entities_from_owl(file_path)
  platform_nodes = []
  for individual in individuals:
    sub_elements = get_sub_elements(individual, graph)    
    belongs_to_predicate = f'http://www.example.com/ontologies/{platform.lower()}-mlops#belongsTo'    
    if belongs_to_predicate in sub_elements:      
      if isinstance(sub_elements[belongs_to_predicate], list):        
        for value in sub_elements[belongs_to_predicate]:
          if value == f'http://www.example.com/ontologies/{platform.lower()}-mlops#{platform}':
            platform_node = individual
            platform_nodes.append(platform_node)
            break  
      else:        
        if sub_elements[belongs_to_predicate] == f'http://www.example.com/ontologies/{platform.lower()}-mlops#{platform}':
          platform_node = individual
          platform_nodes.append(platform_node)

  return platform_nodes

# Compares abstract nodes with sub-elements of platform nodes and stores results in CSVs
def mapped_platform_nodes(file_path, platform):
  individuals, graph = retrieve_entities_from_owl(file_path)

  abstract_nodes = get_abstract_nodes()
  platform_nodes = get_platform_nodes(file_path, platform)
  platform_dataframes = {}

  for abstract_node in abstract_nodes:
    abstract_node_without_prefix = abstract_node.replace('http://www.example.com/ontologies/abstract-mlops#', '')

    for platform_node in platform_nodes:
      subelements = get_sub_elements(platform_node, graph)

      platform_node_prefix_removed = platform_node.replace(f'http://www.example.com/ontologies/{platform.lower()}-mlops#', '')

      if str(RDF.type) in subelements:
        if isinstance(subelements[str(RDF.type)], list):
          if any(abstract_node_without_prefix in value for value in subelements[str(RDF.type)]):
            if platform not in platform_dataframes:              
              platform_dataframes[platform] = pd.DataFrame(columns=['Abstract Node', f'{platform} Node'])  
            new_row = pd.DataFrame({'Abstract Node': [abstract_node_without_prefix], f'{platform} Node': [platform_node_prefix_removed]})
            platform_dataframes[platform] = pd.concat([platform_dataframes[platform], new_row], ignore_index=True)
        else:
          if abstract_node_without_prefix in subelements[str(RDF.type)]:
            if platform not in platform_dataframes:
              platform_dataframes[platform] = pd.DataFrame(columns=['Abstract Node', f'{platform} Node'])  
            new_row = pd.DataFrame({'Abstract Node': [abstract_node_without_prefix], f'{platform} Node': [platform_node_prefix_removed]})
            platform_dataframes[platform] = pd.concat([platform_dataframes[platform], new_row], ignore_index=True)

  for platform, df in platform_dataframes.items():
    df.to_csv(f"{platform}/{platform}_mappings.csv", index=False)

mapped_platform_nodes('AWS/AWS-MLOps.owl', "AWS")
mapped_platform_nodes('Azure/Azure-MLOps.owl', "Azure")
mapped_platform_nodes('Google/Google-MLOps.owl', "Google")


# Checks for abstract node presence in platform CSVs
def check_abstract_node_presence(platform):
  print(platform)
  df = pd.read_csv(f"{platform}/{platform}_mappings.csv")
  abstract_nodes = get_abstract_nodes()
  abstract_nodes_without_prefix = [node.replace('http://www.example.com/ontologies/abstract-mlops#', '') for node in abstract_nodes]

  missing_nodes = set(abstract_nodes_without_prefix) - set(df['Abstract Node'])

  if missing_nodes:
    print(f"{platform} is not a full instantiation of the abstract model.")
    print(f"The following abstract model nodes are not included in the {platform} model:")
    for node in missing_nodes:
      print(f"- {node}")
  else:
    print(f"{platform} is a full instantiation of the abstract model.")
    print(f"All abstract model nodes are included in the {platform} model.")

print("\n")
check_abstract_node_presence("AWS")
print("\n")
check_abstract_node_presence("Azure")
print("\n")
check_abstract_node_presence("Google")


# Whitelisting platform nodes without mappings to abstract nodes
def get_unmapped_platform_nodes(file_path, platform):
  print(platform)
  df = pd.read_csv(f"{platform}/{platform}_mappings.csv")
  platform_nodes = get_platform_nodes(file_path, platform)

  platform_nodes_without_prefix = [node.replace(f'http://www.example.com/ontologies/{platform.lower()}-mlops#', '') for node in platform_nodes]

  unmapped_nodes = set(platform_nodes_without_prefix) - set(df[f'{platform} Node'])

  if unmapped_nodes:
    print(f"The following nodes are specific to the {platform} model and do not appear in the Abstract model")
    for node in unmapped_nodes:
      print(f"- {node}")
  else:
    print(f"All platform nodes in the {platform} model have corresponding mappings to abstract nodes.")

print("\n")
get_unmapped_platform_nodes('AWS/AWS-MLOps.owl', "AWS")
print("\n")
get_unmapped_platform_nodes('Azure/Azure-MLOps.owl', "Azure")
print("\n")
get_unmapped_platform_nodes('Google/Google-MLOps.owl', "Google")


# Merging platform-specific DataFrames
def merge_dataframes():
  dfs = []
  for platform in ['AWS', 'Azure', 'Google']:
    df = pd.read_csv(f"{platform}/{platform}_mappings.csv").fillna('N/A')  
    dfs.append(df)

  combined_df = dfs[0].merge(dfs[1], on='Abstract Node', how='outer').fillna('N/A')  
  combined_df = combined_df.merge(dfs[2], on='Abstract Node', how='outer').fillna('N/A')  

  combined_df.to_csv("Files/combined_mappings.csv", index=False)

merge_dataframes()


# Verifying the Abstract to Platforms mapping table programatically
def abstract_to_platform_verification():
  df_abstract_platforms = pd.read_csv('Abstract/Abstract_to_Platforms_Table.csv')
  df_combined_mappings = pd.read_csv('Files/combined_mappings.csv')
  df_combined_mappings = df_combined_mappings.applymap(lambda x: x.replace('_', ' ') if isinstance(x, str) else x)

  row_lists_abstract_platforms = df_abstract_platforms.values.tolist()
  row_lists_combined_mappings = df_combined_mappings.values.tolist()

  all_rows_verified = True
  for row_abstract in row_lists_abstract_platforms:
    if row_abstract not in row_lists_combined_mappings:
      all_rows_verified = False
      print(f"Row not found in combined mappings: {row_abstract}")
      break

  if all_rows_verified:
    print("All nodes verified! The Abstract to Platforms mapping is verified programatically")
  else:
    print("Verification failed! Some nodes are not matching")

print("\n")
abstract_to_platform_verification()



# Properties
print("\n")
print("Verifying Properties")


# Get properties of the specified platform
def get_all_properties(file_path, platform):
    g = Graph()
    g.parse(file_path)
    prefix = f"http://www.example.com/ontologies/{platform}-mlops#"
    properties = set()
    for prop in g.subjects(RDF.type, OWL.ObjectProperty):
        prop_str = str(prop).replace(prefix, '')
        properties.add(prop_str)
    for prop in g.subjects(RDF.type, OWL.DatatypeProperty):
        prop_str = str(prop).replace(prefix, '')
        properties.add(prop_str)
    
    return properties


Abstract_properties = get_all_properties("Abstract/Abstract-MLOps.owl", "abstract")
AWS_properties = get_all_properties("AWS/AWS-MLOps.owl", "aws")
Azure_properties = get_all_properties("Azure/Azure-MLOps.owl", "azure")
Google_properties = get_all_properties("Google/Google-MLOps.owl", "google")


# Compares if all the abstract properties appear in the concrete models
def compare_properties(abstract_properties, platform_properties, platform):
  print("\n")
  print(platform)
  if abstract_properties.issubset(platform_properties):
    print(f"All abstract properties are present in {platform} properties.")
  else:
    missing_properties = abstract_properties - platform_properties
    print(f"Some abstract properties are missing in {platform} properties:")
    for prop in missing_properties:
      print(prop)


compare_properties(Abstract_properties, AWS_properties, "AWS")
compare_properties(Abstract_properties, Azure_properties, "Azure")
compare_properties(Abstract_properties, Google_properties, "Google")


# Whitelisting the properties that are specific to the platforms
def concrete_properties(abstract_properties, platform_properties, platform):
  print("\n")
  print(platform)  
  platform_specific_properties = platform_properties - abstract_properties
  if platform_specific_properties:
    print(f"\nPlatform-specific properties {platform}:")
    for prop in platform_specific_properties:
      print(prop)


concrete_properties(Abstract_properties, AWS_properties, "AWS")
concrete_properties(Abstract_properties, Azure_properties, "Azure")
concrete_properties(Abstract_properties, Google_properties, "Google")