#!/bin/bash

# Script to recursively delete files with a specified extension in a given directory, with an option to preview the files

# Function to display help
show_help() {
    echo "Usage: $0 [-p] <start_directory> <extension>"
    echo
    echo "This script recursively deletes all files with a specified extension"
    echo "within the given directory and its subdirectories."
    echo "Use the -p option to preview the files that would be deleted."
    echo
    echo "Options:"
    echo "  -p    Preview the files to be deleted, without actually deleting them."
    echo
    echo "Arguments:"
    echo "  start_directory: The directory where the search and deletion will begin."
    echo "                   This can be an absolute or a relative path."
    echo "  extension:       The file extension of the files to delete."
    echo "                   Include the extension without the dot (.) before it."
    echo
    echo "Example:"
    echo "  $0 /path/to/directory txt"
    echo "  This will delete all .txt files in /path/to/directory and its subdirectories."
    echo
    echo "  $0 -p /path/to/directory txt"
    echo "  This will preview all .txt files in /path/to/directory and its subdirectories."
}

# Check if at least two arguments are provided
if [ "$#" -lt 2 ]; then
    show_help
    exit 1
fi

# Check for the presence of -h or --help
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Preview mode flag
PREVIEW_MODE=false

# Check for the presence of -p option
if [ "$1" = "-p" ]; then
    PREVIEW_MODE=true
    shift # Shift arguments to the left
fi

# Assign the arguments to START_DIR and EXTENSION
START_DIR=$1
EXTENSION=$2

# Find and either preview or remove files with the given extension in the specified directory
if $PREVIEW_MODE; then
    echo "Previewing files to be deleted:"
    find "$START_DIR" -type f -name "*.$EXTENSION"
else
    find "$START_DIR" -type f -name "*.$EXTENSION" -exec rm {} +
fi

# The script ends here
