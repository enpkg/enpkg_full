#!/bin/bash

# Script to recursively preview or delete files and directories with a specified pattern in a given directory

# Function to display help
show_help() {
    echo "Usage: $0 [-p] <start_directory> <pattern>"
    echo
    echo "This script recursively deletes or previews all files and directories with a specified pattern"
    echo "within the given directory and its subdirectories."
    echo
    echo "Options:"
    echo "  -p    Preview the files and directories to be deleted, without actually deleting them."
    echo
    echo "Arguments:"
    echo "  start_directory: The directory where the search will begin."
    echo "                   This can be an absolute or a relative path."
    echo "  pattern:         The file and directory pattern to delete or preview."
    echo "                   Do not include the dot (.) before the pattern."
    echo
    echo "Example:"
    echo "  $0 /path/to/directory txt"
    echo "  This will delete all .txt files and directories containing 'txt' in /path/to/directory and its subdirectories."
    echo
    echo "  $0 -p /path/to/directory txt"
    echo "  This will preview all .txt files and directories containing 'txt' in /path/to/directory and its subdirectories."
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

# Assign the arguments to START_DIR and PATTERN
START_DIR=$1
PATTERN=$2

# Find and either preview or remove files and directories with the given pattern in the specified directory
if $PREVIEW_MODE; then
    echo "Previewing files and directories to be deleted:"
    find "$START_DIR" -type f -name "*$PATTERN*" -print
    find "$START_DIR" -type d -name "*$PATTERN*" -print
else
    find "$START_DIR" -type f -name "*$PATTERN*" -exec rm {} +
    find "$START_DIR" -type d -name "*$PATTERN*" -exec rm -r {} +
fi

# The script ends here
