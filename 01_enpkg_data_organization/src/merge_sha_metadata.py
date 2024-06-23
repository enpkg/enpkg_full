import pandas as pd
import argparse

def merge_files(tsv_file, csv_file, output_file):
    # Read the TSV file
    tsv_data = pd.read_csv(tsv_file, sep='\t')

    # Read the CSV file
    csv_data = pd.read_csv(csv_file)

    # Merge the files on the 'sample_filename' column
    merged_data = pd.merge(tsv_data, csv_data, on='sample_filename', how='inner')

    # Write the merged data to a new TSV file
    merged_data.to_csv(output_file, sep='\t', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Merge TSV and CSV files on sample_filename column.')
    parser.add_argument('tsv_file', type=str, help='Input TSV file')
    parser.add_argument('csv_file', type=str, help='Input CSV file')
    parser.add_argument('output_file', type=str, help='Output merged TSV file')

    args = parser.parse_args()

    merge_files(args.tsv_file, args.csv_file, args.output_file)
