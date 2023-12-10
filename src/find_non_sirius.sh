#!/bin/bash

# Script to find and optionally delete directories containing "_WORKSPACE_SIRIUS" without "compound_identifications.tsv" file

# Function to display help
show_help() {
    echo "Usage: $0 [-d] <top_level_dir>"
    echo
    echo "This script searches for directories containing '_WORKSPACE_SIRIUS' in their name"
    echo "and checks if 'compound_identifications.tsv' does not exist in these directories."
    echo "Use the -d option to actually delete these directories."
    echo
    echo "Options:"
    echo "  -d    Delete the directories instead of just echoing their paths."
    echo
    echo "Arguments:"
    echo "  top_level_dir: The top-level directory where the search will begin."
    echo
    echo "Example:"
    echo "  $0 /path/to/top-level-directory"
    echo "  This will display directories for potential deletion."
    echo
    echo "  $0 -d /path/to/top-level-directory"
    echo "  This will delete the directories."
}

# Check if at least one argument is provided
if [ "$#" -lt 1 ]; then
    show_help
    exit 1
fi

# Delete mode flag
DELETE_MODE=false

# Check for the presence of -d option
if [ "$1" = "-d" ]; then
    DELETE_MODE=true
    shift # Shift arguments to the left
fi

# Check if top-level directory is provided after option processing
if [ "$#" -ne 1 ]; then
    show_help
    exit 1
fi

# Assign the argument to top_level_dir
top_level_dir=$1

# Find directories containing "_WORKSPACE_SIRIUS" in their name
find "$top_level_dir" -type d -name "*_WORKSPACE_SIRIUS*" | while read -r dir_path
do
  # Check if 'compound_identifications.tsv' does NOT exist in this directory tree
  if ! find "$dir_path" -name "compound_identifications.tsv" | grep -q .
  then
    if $DELETE_MODE; then
      rm -r "$dir_path"
      echo "Deleted $dir_path"
    else
      echo "Target directory for deletion: $dir_path"
    fi
  fi
done
