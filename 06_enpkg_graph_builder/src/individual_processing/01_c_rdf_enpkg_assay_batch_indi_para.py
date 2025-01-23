import os
from pathlib import Path
import yaml
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from tqdm import tqdm

def substitute_variables(config):
    """Recursively substitute variables in the YAML configuration."""
    def substitute(value, context):
        if isinstance(value, str):
            for key, replacement in context.items():
                value = value.replace(f"${{{key}}}", replacement)
        return value

    def recurse_dict(d, context):
        for key, value in d.items():
            if isinstance(value, dict):
                recurse_dict(value, context)
            else:
                d[key] = substitute(value, context)

    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"],
    }
    recurse_dict(config, context)
    return config

# Load parameters
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    sys.exit(1)

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list_full = substitute_variables(params_list_full)

# Extract parameters
sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = "ttl"

# Define namespaces
<<<<<<< Updated upstream
JLW = Namespace("http://example.org/jlw#")
=======
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']
>>>>>>> Stashed changes
PROV = Namespace("http://www.w3.org/ns/prov#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

# Validate sample directory path
if not os.path.exists(sample_dir_path):
    print(f"Sample directory path not found: {sample_dir_path}")
    sys.exit(1)

samples_dir = [directory for directory in os.listdir(sample_dir_path) if not directory.startswith('.')]

def process_directory(directory):
    g = Graph()
<<<<<<< Updated upstream
    g.namespace_manager.bind("jlw", JLW)
    g.namespace_manager.bind("prov", PROV)
    g.namespace_manager.bind("dcat", DCAT)
=======
    nm = g.namespace_manager
    nm.bind("prov", PROV)
    nm.bind("dcat", DCAT)
    nm.bind(prefix, ns_kg)
>>>>>>> Stashed changes

    try:
        batch_polarity = params_list_full['general']['polarity']
        batch_label = params_list_full['assay-batch']['batch_comment']
        batch_instrument = params_list_full['assay-batch']['batch_instrument']
        batch_date = params_list_full['assay-batch']['batch_date']
        batch_operator = params_list_full['assay-batch']['batch_operator']
        batch_url = params_list_full['assay-batch']['batch_url']

        batch_id = f"assay_batch_{batch_polarity.lower()}"
<<<<<<< Updated upstream
        batch_node = JLW[batch_id]

        g.add((batch_node, RDF.type, JLW.AssayBatch))
        g.add((batch_node, RDFS.label, Literal(batch_label)))
        g.add((batch_node, PROV.generatedAtTime, Literal(batch_date, datatype=XSD.gYearMonth)))
        g.add((batch_node, JLW.has_instrument_type, Literal(batch_instrument)))
        g.add((batch_node, DCAT.accessURL, URIRef(batch_url)))
        g.add((batch_node, JLW.has_operator, JLW[batch_operator.replace(' ', '_')]))
=======
        batch_node = ns_kg[batch_id]

        g.add((batch_node, RDF.type, JLW.AssayBatch))
        g.add((batch_node, RDFS.label, Literal(batch_label)))
        g.add((batch_node, ns_kg.generatedAtTime, Literal(batch_date, datatype=XSD.gYearMonth)))
        g.add((batch_node, ns_kg.has_instrument_type, Literal(batch_instrument)))
        g.add((batch_node, DCAT.accessURL, URIRef(batch_url)))
        g.add((batch_node, ns_kg.has_operator, JLW[batch_operator.replace(' ', '_')]))
>>>>>>> Stashed changes

        # Write to file
        pathout = os.path.join(sample_dir_path, directory, "rdf/")
        os.makedirs(pathout, exist_ok=True)
        pathout = os.path.join(pathout, f"{batch_id}.{output_format}")
        g.serialize(destination=pathout, format=output_format, encoding="utf-8")
        print(f"Results are in: {pathout}")

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}"
        print(error_message)
        return error_message


def main():
    for directory in tqdm(samples_dir, desc="Processing directories"):
        process_directory(directory)

if __name__ == "__main__":
<<<<<<< Updated upstream
    main()
=======
    main()
>>>>>>> Stashed changes
