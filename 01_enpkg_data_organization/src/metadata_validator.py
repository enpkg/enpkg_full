import argparse
from pprint import pprint
from frictionless import validate, Schema, errors

# Define the schema for the required columns
schema_descriptor = {
    "fields": [
        {"name": "sample_filename_pos", "type": "string"},
        {"name": "sample_filename_neg", "type": "string"},
        {"name": "sample_id", "type": "string"},
        {"name": "sample_type", "type": "string"},
        {"name": "source_id", "type": "string"},
        {"name": "source_taxon", "type": "string"}
    ],
    "header": True
}
schema = Schema(schema_descriptor)

def validate_tsv_file(file_path):
    # Validate the TSV file against the schema
    try:
        report = validate(file_path, schema=schema)
        if report.valid:
            print(f"The TSV file '{file_path}' is valid and contains the required columns.")
        else:
            print(f"The TSV file '{file_path}' is invalid.")
            pprint(report.flatten(["rowPosition", "fieldPosition", "code", "message"]))
    except Exception as e:
        print(f"An error occurred during validation: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a TSV file against a schema.")
    parser.add_argument("file_path", help="Path to the TSV file")

    args = parser.parse_args()

    # Validate the TSV file
    validate_tsv_file(args.file_path)
