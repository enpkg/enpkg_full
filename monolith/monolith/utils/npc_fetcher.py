import requests
import logging
from urllib.parse import quote
import duckdb
import pandas as pd
from tqdm import tqdm


# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("npc_classification.log"),  # Log to a file
        # logging.StreamHandler()  # Also log to console
    ],
)


# Modified get_npc_classification function with simple retry mechanism
def get_npc_classification(smiles, max_retries=3):

    # URL encode the SMILES string
    encoded_smiles = quote(smiles)

    url = f"https://npclassifier.gnps2.org/classify?smiles={encoded_smiles}"
    retries = 0

    while retries < max_retries:
        try:
            response = requests.get(
                url, timeout=10
            )  # Adding a timeout to avoid hanging
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(
                    f"Error fetching data for SMILES: {smiles} - Status Code: {response.status_code}"
                )
                break
        except requests.exceptions.RequestException as e:
            retries += 1
            logging.error(f"Attempt {retries} failed for SMILES: {smiles} - {e}")

    logging.error(
        f"Failed to fetch data for SMILES: {smiles} after {max_retries} attempts."
    )
    return None


# Function to initialize DuckDB and create a table if not exists
def initialize_duckdb(db_name="npc_classification.duckdb"):
    conn = duckdb.connect(db_name)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS npc_classification (
            inchikey TEXT,
            smiles TEXT PRIMARY KEY,
            npc_pathway TEXT,
            npc_superclass TEXT,
            npc_class TEXT
        )
    """
    )
    conn.close()


# Function to get the processed SMILES from DuckDB
def get_processed_smiles(db_name="npc_classification.duckdb"):
    conn = duckdb.connect(db_name)
    result = conn.execute("SELECT smiles FROM npc_classification").fetchall()
    processed = {row[0] for row in result}
    conn.close()
    return processed


# Function to save results to DuckDB
def save_results_to_duckdb(results, db_name="npc_classification.duckdb"):
    conn = duckdb.connect(db_name)
    conn.executemany(
        """
        INSERT INTO npc_classification (inchikey, smiles, npc_pathway, npc_superclass, npc_class)
        VALUES (?, ?, ?, ?, ?)
    """,
        results,
    )
    conn.close()


# Function to classify and add NPC levels to the DataFrame in batches
def process_npc_classification(
    df,
    inchikey_column="structure_inchikey",
    smiles_column="structure_smiles",
    batch_size=1000,
    db_name="npc_classification.duckdb",
):
    # Initialize DuckDB
    initialize_duckdb(db_name)

    # Get already processed SMILES
    processed_smiles = get_processed_smiles(db_name)

    # Filter the DataFrame to only process unprocessed SMILES
    df_to_process = df[~df[smiles_column].isin(processed_smiles)]
    num_rows_to_process = len(df_to_process)

    # Check if there are rows to process
    if num_rows_to_process == 0:
        logging.info("All rows have been processed already. No new data to process.")
        return

    # Calculate the number of batches
    total_batches = (num_rows_to_process - 1) // batch_size + 1

    # Outer tqdm for the entire DataFrame processing
    with tqdm(total=total_batches, desc="Processing batches") as outer_pbar:
        # Iterate over DataFrame in batches
        for start in range(0, num_rows_to_process, batch_size):
            end = min(start + batch_size, num_rows_to_process)
            batch = df_to_process.iloc[start:end]

            results = []

            # Inner tqdm for each batch processing
            with tqdm(
                total=len(batch),
                desc=f"Processing batch {start//batch_size + 1}",
                leave=False,
            ) as inner_pbar:
                for index in range(len(batch)):
                    row = batch.iloc[index]
                    smiles = row[smiles_column]
                    inchikey = row[inchikey_column]

                    # Log the start of processing for the current InChIKey
                    logging.info(f"Processing InChIKey: {inchikey}")

                    npc_result = get_npc_classification(smiles)

                    if npc_result:
                        npc_pathway = (
                            ", ".join(npc_result["pathway_results"])
                            if npc_result["pathway_results"]
                            else None
                        )
                        npc_superclass = (
                            ", ".join(npc_result["superclass_results"])
                            if npc_result["superclass_results"]
                            else None
                        )
                        npc_class = (
                            ", ".join(npc_result["class_results"])
                            if npc_result["class_results"]
                            else None
                        )
                        results.append(
                            (inchikey, smiles, npc_pathway, npc_superclass, npc_class)
                        )

                        # Log the successful processing of the InChIKey
                        logging.info(f"Successfully processed InChIKey: {inchikey}")

                    # Update the inner progress bar
                    inner_pbar.update(1)

            # Save the batch results to the DuckDB database
            save_results_to_duckdb(results, db_name)
            # Update the outer progress bar after completing each batch
            outer_pbar.update(1)


# Function to keep only unique inchikeys, npclassifier_01pathway combinations and return the full dataframe.


def unique_inchikey_pathway(metadata):
    metadata_unique = metadata.drop_duplicates(
        subset=["structure_inchikey", "structure_taxonomy_npclassifier_01pathway"]
    )
    print(f"Number of unique inchikey-pathway combinations: {metadata_unique.shape[0]}")

    return metadata_unique


def unique_inchikey(metadata):
    metadata_unique = metadata.drop_duplicates(subset=["structure_inchikey"])
    print(f"Number of unique inchikey: {metadata_unique.shape[0]}")

    return metadata_unique


# Example usage:
# process_npc_classification(metadata_unique_ik[:300], inchikey_column='structure_inchikey', smiles_column='structure_smiles', batch_size=100, db_name='npc_classification.duckdb')


def get_classification_results(db_name="monolith/npc_classification.duckdb"):
    # Connect to the DuckDB database
    conn = duckdb.connect(db_name)

    # Query to retrieve all the data from the npc_classification table
    query = """
    SELECT inchikey, smiles, npc_pathway, npc_superclass, npc_class
    FROM npc_classification
    """

    # Execute the query and fetch the results as a Pandas DataFrame
    df_results = conn.execute(query).fetchdf()

    # Close the connection
    conn.close()

    return df_results


# Example usage:
# df_classifications = get_classification_results()
# print(df_classifications.head())

# if name == "__main__": to launch the script from the command line

if __name__ == "__main__":
    print("Loading metadata...")
    # Load your dataset into a DataFrame
    path_to_lotus = "downloads/unclassified_inchikeys.csv"
    # Load the metadata table
    metadata = pd.read_csv(path_to_lotus)
    print("Keeping only unique InChIKeys...")
    metadata_unique_ik = unique_inchikey(metadata)
    print("Running NPC classification script...")
    process_npc_classification(
        metadata_unique_ik,
        inchikey_column="structure_inchikey",
        smiles_column="structure_smiles",
        batch_size=1000,
        db_name="npc_classification.duckdb",
    )
