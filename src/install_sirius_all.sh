#!/bin/bash

# Exit on error
set -e

# Check if at least two arguments are provided (the platform and the output location)
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <platform> <output_location>"
    echo "Platforms: linux, osx"
    exit 1
fi

platform="$1"
output_location="$2"

# Validate platform
if [[ "$platform" != "linux" ]] && [[ "$platform" != "osx" ]]; then
    echo "Error: Invalid platform specified. Use 'linux' or 'osx'."
    exit 1
fi

# Confirm that necessary commands are available
for cmd in wget jq unzip curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd is required but not installed. Please install it and try again." >&2
        exit 1
    fi
done

echo "Fetching the latest version of Sirius for $platform..."

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

# Fetch release information
release_info=$(curl -s "$api_url")


# Get the download URL for the platform-specific version, excluding .sha256 files
download_url=$(echo "$release_info" | jq -r '.assets[] | select(.name | test("'$platform'.*\\.zip$")) | .browser_download_url')



if [ -z "$download_url" ]; then
    echo "Error: Could not find a $platform zip version of the latest release."
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

# Extracting the directory name of the unzipped folder (assuming it's the only directory extracted)
dir_name=$(unzip -qql "$filename" | head -n1 | tr -s ' ' | cut -d' ' -f5- | cut -d'/' -f1)

# Check if the output location doesn't exist and create it
if [ ! -d "$output_location" ]; then
    mkdir -p "$output_location"
fi


# Extracting the directory name of the unzipped folder (assuming it's the only directory extracted)
dir_name=$(unzip -qql "$filename" | head -n1 | tr -s ' ' | cut -d' ' -f5- | cut -d'/' -f1)

# Check if the output location doesn't exist and create it
if [ ! -d "$output_location" ]; then
    mkdir -p "$output_location"
fi

# Move the Sirius directory to the desired output location
install_dir="$output_location/$dir_name"
mv "$dir_name" "$output_location"

echo "Sirius has been moved to $install_dir."

# Set the path to the Sirius executable based on the platform
if [ "$platform" = "osx" ]; then
    executable_path="$install_dir/Contents/MacOS/sirius"
else
    executable_path="$install_dir/sirius/bin"
fi

# Inform the user about the next steps, like how to add the directory to their PATH permanently
echo "You might want to add $executable_path to your PATH variable for easier access."
echo "You can do this by adding the following line to your ~/.bashrc or ~/.profile file:"
echo "export PATH=\$PATH:$executable_path"

# Final message to guide the user on how to use Sirius
echo "You can start Sirius by running 'sirius' from the $executable_path directory."
echo "For more information on how to use Sirius, please refer to the official documentation."
