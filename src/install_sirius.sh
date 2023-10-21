#!/bin/bash

# Exit on error
set -e

# Confirm that necessary commands are available
for cmd in wget jq unzip curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd is required but not installed. Please install it and try again." >&2
        exit 1
    fi
done

echo "Fetching the latest version of Sirius for Linux..."

# GitHub's API URL for the latest release
api_url="https://api.github.com/repos/boecker-lab/sirius/releases/latest"

# Fetch release information
release_info=$(curl -s "$api_url")

# Check if assets are available
assets=$(echo "$release_info" | jq '.assets')
if [[ $assets == "null" ]] || [[ $assets == "[]" ]]; then
    echo "Error: No assets found for the latest release. The release might be a draft or pre-release."
    exit 1
fi

# Get the download URL for the Linux zip version, excluding .sha256 files
download_url=$(echo "$release_info" | jq -r '.assets[] | select(.name | test("linux.*\\.zip$")) | .browser_download_url')

if [ -z "$download_url" ]; then
    echo "Error: Could not find a Linux zip version of the latest release."
    exit 1
fi

# Extract the filename of the package to download
filename=$(basename "$download_url")

# Download the release package
if wget -O "$filename" "$download_url"; then
    echo "Downloaded $filename."
else
    echo "Failed to download Sirius." >&2
    exit 1
fi

# Unzip the downloaded file
if [[ $filename == *.zip ]]; then
    unzip "$filename"
    echo 'Extraction complete.'
else
    echo "The downloaded file is not a zip file. Please handle it manually."
    exit 1
fi

echo 'Sirius installation file is ready.'
# Add additional installation steps if necessary. It might involve moving files to certain directories or setting permissions.
