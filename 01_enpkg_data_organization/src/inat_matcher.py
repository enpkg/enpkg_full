import argparse
import pandas as pd

def merge_csv_files(file_a, column_a, file_b, column_b, output_file):
    # Read the CSV files
    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)
    
    # Perform a left join based on column names
    merged_df = pd.merge(df_a, df_b, left_on=column_a, right_on=column_b, how='left')
    
    # Write the merged DataFrame to a TSV file
    merged_df.to_csv(output_file, sep='\t', index=False)
    
    print(f"Merged CSV file '{output_file}' created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform a left join on two CSV files based on specified columns.")
    parser.add_argument('--file_a', required=True, help='Path to the first CSV file')
    parser.add_argument('--column_a', required=True, help='Column name in the first CSV file')
    parser.add_argument('--file_b', required=True, help='Path to the second CSV file')
    parser.add_argument('--column_b', required=True, help='Column name in the second CSV file')
    parser.add_argument('--output_file', required=True, help='Path to the output merged CSV file')
    
    args = parser.parse_args()
    
    # Merge the CSV files with a left join
    merge_csv_files(args.file_a, args.column_a, args.file_b, args.column_b, args.output_file)
