#!/bin/bash

# Script to recursively delete files with a specified extension in a given directory

# Function to display help
show_help() {
    echo "Usage: $0 <start_directory> <extension>"
    echo
    echo "This script recursively deletes all files with a specified extension"
    echo "within the given directory and its subdirectories."
    echo
    echo "Arguments:"
    echo "  start_directory: The directory where the search and deletion will begin."
    echo "                   This can be an absolute or a relative path."
    echo "  extension:       The file extension of the files to delete."
    echo "                   Do not include the dot (.) before the extension."
    echo
    echo "Example:"
    echo "  $0 /path/to/directory txt"
    echo "This will delete all .txt files in /path/to/directory and its subdirectories."
}

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    show_help
    exit 1
fi

# Check for the presence of -h or --help
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Assign the first argument to START_DIR and the second to EXTENSION
START_DIR=$1
EXTENSION=$2

# Find and remove files with the given extension in the specified directory
find "$START_DIR" -type f -name "*.$EXTENSION" -exec rm {} +

# The script ends here
