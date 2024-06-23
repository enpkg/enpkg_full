import os
import csv
import xml.etree.ElementTree as ET
import argparse
from tqdm import tqdm

def extract_sha_values(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Namespaces in mzML files
    ns = {'mzml': 'http://psi.hupo.org/ms/mzml'}

    # Initialize the values
    raw_sha = None
    converted_sha = None

    # Find the raw_sha
    for cvParam in root.findall('.//mzml:cvParam', ns):
        if cvParam.attrib.get('accession') == 'MS:1000569':
            raw_sha = cvParam.attrib.get('value')
            break

    # Find the converted_sha
    for fileChecksum in root.findall('.//mzml:fileChecksum', ns):
        converted_sha = fileChecksum.text
        break

    return raw_sha, converted_sha

def process_directory(directory_path, output_csv):
    files = [f for f in os.listdir(directory_path) if f.endswith('.mzML')]

    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['sample_filename', 'raw_sha', 'converted_sha']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for filename in tqdm(files, desc="Processing files"):
            file_path = os.path.join(directory_path, filename)
            raw_sha, converted_sha = extract_sha_values(file_path)
            writer.writerow({
                'sample_filename': filename,
                'raw_sha': raw_sha,
                'converted_sha': converted_sha
            })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process mzML files and extract SHA values.')
    parser.add_argument('directory', type=str, help='Directory containing mzML files')
    parser.add_argument('output_csv', type=str, help='Output CSV file')

    args = parser.parse_args()

    process_directory(args.directory, args.output_csv)
