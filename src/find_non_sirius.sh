#!/bin/bash

# Replace with the path to the top-level directory you want to search in
top_level_dir="/home/allardpm/ENPKG/data/MSV000085119_pos_treated"

# Find directories containing "_WORKSPACE_SIRIUS" in their name
find "$top_level_dir" -type d -name "*_WORKSPACE_SIRIUS*" | while read -r dir_path
do
  # Check if 'compound_identifications.tsv' does NOT exist in this directory tree
  if ! find "$dir_path" -name "compound_identifications.tsv" | grep -q .
  then
    echo "Target directory for deletion: $dir_path"
    
    # Uncomment the line below to actually perform the deletion operation
    # rm -r "$dir_path"
    # echo "Deleted $dir_path"
  fi
done