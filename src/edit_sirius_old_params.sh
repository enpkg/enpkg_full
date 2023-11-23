#!/bin/bash

# Function to show help information
show_help() {
    echo "Usage: $(basename $0) [-h] [-d directory]"
    echo "  -h  Show this help message"
    echo "  -d  Specify the root directory to search for params.yml files"
}

# Default root directory (change this to a default path if needed)
root_directory=""

# Process command-line options
while getopts 'hd:' option; do
    case "$option" in
        h) show_help
           exit ;;
        d) root_directory=$OPTARG ;;
        *) show_help
           exit 1 ;;
    esac
done

# Check if root directory is provided
if [ -z "$root_directory" ]; then
    echo "Error: Root directory is not specified."
    show_help
    exit 1
fi

# Find directories ending with _SIRIUS and modify params.yml in each
find "$root_directory" -type d -name "*_SIRIUS" | while read dir; do
    params_file="$dir/params.yml"
    if [ -f "$params_file" ]; then
        echo "Processing folder: $dir"
        # Use sed to replace "  - " with "  " and save changes
        sed -i 's/  - /  /g' "$params_file"
    else
        echo "No params.yml found in: $dir"
    fi
done

echo "Processing complete."
