#!/bin/bash


# Exit on error
set -e

# Check if version argument is provided
version=$1

# Default to latest version if no argument is provided
if [ -z "$version" ]; then
    echo "No version provided, fetching the latest version of Sirius."
    api_url="https://api.github.com/repos/sirius-ms/sirius/releases/latest"
else
    echo "Fetching version $version of Sirius."
    api_url="https://api.github.com/repos/sirius-ms/sirius/releases/tags/$version"
fi

# Fetch release information
release_info=$(curl -s "$api_url")

# Debug: Print release_info to check if we get a valid response from GitHub
echo "Release info: $release_info"

# Check if assets are available
assets=$(echo "$release_info" | jq '.assets')
if [ "$assets" == "null" ] || [ "$assets" == "[]" ]; then
    echo "Error: No assets found for the release. The release might not exist or be a draft."
    exit 1
fi

# Get the download URL for the Linux zip version, excluding .sha256 files
download_url=$(echo "$release_info" | jq -r '.assets[] | select(.name | test("linux.*\\.zip$")) | .browser_download_url')

if [ -z "$download_url" ]; then
    echo "Error: Could not find a Linux zip version of the release."
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
if [ "${filename: -4}" == ".zip" ]; then
    unzip "$filename"
    echo 'Extraction complete.'
else
    echo "The downloaded file is not a zip file. Please handle it manually."
    exit 1
fi

echo 'Sirius installation file is ready.'
# Add additional installation steps if necessary. It might involve moving files to certain directories or setting permissions.
