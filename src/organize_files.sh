#!/bin/bash

# Directory where your files are located
SOURCE_DIR="/home/allardpm/ENPKG/data/pf1600/pf1600_reprocess_annex/standalone_graphs"

# Change to the directory with the files
cd "$SOURCE_DIR"

# Loop over the .ttl.gz files
for file in *.ttl.gz; do
    # Extract the plate identifier (e.g., VGF144)
    PLATE=$(echo "$file" | awk -F '_' '{print $2}')

    # Create a directory for the plate if it doesn't exist
    if [ ! -d "$PLATE" ]; then
        mkdir "$PLATE"
    fi

    # Move the file into its respective plate directory
    mv "$file" "$PLATE/"
done

echo "Files have been organized into folders."
