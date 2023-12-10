#!/bin/bash

# Script to recursively delete files with a specified extension in a given directory

# Function to display help
show_help() {
    echo "Usage: $0 <start_directory>"
    echo
    echo "This script recursively deletes all files and directories "
    echo "within the given directory and its subdirectories."
    echo
    echo "Arguments:"
    echo "  start_directory: The directory where the search and deletion will begin."
    echo "                   This can be an absolute or a relative path."
    echo
    echo "Example:"
    echo "  $0 /path/to/directory"
    echo "This will delete all /pos/isdb and /pos/molecular_network directories in /path/to/directory and its subdirectories."
    echo
    echo "You can use the -h or --help flag to display this help message."
    echo "Furthermore you need to provide a directory as an argument."
}

# Check if help is requested

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Only run if a directory is provided as an argument

if [ "$#" -ne 1 ]; then
    show_help
    exit 1
fi


# Define the path to the directory containing all your directories
PARENT_DIR=$1


# Loop through all directories within the parent directory
for DIR in ${PARENT_DIR}/*; do
    if [ -d "${DIR}" ]; then # If it's a directory
        # Navigate to dir/pos

        cd "${DIR}/pos"

        # remove files and dir for the dir called "isdb"
        rm -r isdb

        # remove files and dir for the dir called "molecular_network"
        rm -r molecular_network

        # Optional: Output some status messages
        echo "ISDB output removed from ${DIR}/pos"
    fi
done

# End of script
