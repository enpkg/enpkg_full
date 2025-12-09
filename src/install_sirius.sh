#!/bin/bash

# Exit on error
set -e

# Check if at least one argument is provided (the output location)
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <output_location> [platform] [architecture]"
    echo "  platform: linux|macos (optional, auto-detected)"
    echo "  architecture: x64|arm64 (optional, auto-detected)"
    exit 1
fi

output_location="$1"

# Allow optional platform override via second argument
requested_platform="${2:-auto}"
# Allow optional architecture override via third argument
requested_arch="${3:-auto}"

# Confirm that necessary commands are available
for cmd in wget jq unzip curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd is required but not installed. Please install it and try again." >&2
        exit 1
    fi
done

detected_os=$(uname -s)
case "$requested_platform" in
    linux|Linux) platform="linux" ;;
    mac|macos|darwin|Mac|MacOS|Darwin) platform="macos" ;;
    auto)
        if [[ "$detected_os" == "Linux" ]]; then
            platform="linux"
        elif [[ "$detected_os" == "Darwin" ]]; then
            platform="macos"
        else
            echo "Error: Unsupported platform '$detected_os'. Please rerun with an explicit platform (linux|macos)." >&2
            exit 1
        fi
        ;;
    *)
        echo "Error: Unknown platform override '$requested_platform'. Supported values: linux, macos." >&2
        exit 1
        ;;
esac

detected_arch=$(uname -m)
case "$requested_arch" in
    auto)
        if [[ "$detected_arch" == "x86_64" || "$detected_arch" == "amd64" ]]; then
            arch="x64"
        elif [[ "$detected_arch" == "arm64" || "$detected_arch" == "aarch64" ]]; then
            arch="arm64"
        else
            arch="any"
        fi
        ;;
    x64|X64|x86_64|amd64) arch="x64" ;;
    arm64|Arm64|aarch64) arch="arm64" ;;
    any|Any|universal|Universal) arch="any" ;;
    *)
        echo "Error: Unknown architecture override '$requested_arch'. Supported values: x64, arm64." >&2
        exit 1
        ;;
esac

if [[ "$platform" == "linux" ]]; then
    base_pattern="(?i)linux"
    platform_label="Linux"
else
    base_pattern="(?i)(mac|osx|darwin)"
    platform_label="macOS"
fi

if [[ "$arch" == "any" ]]; then
    asset_pattern="${base_pattern}.*\\.zip$"
else
    asset_pattern="${base_pattern}.*-${arch}.*\\.zip$"
fi

echo "Fetching the latest version of Sirius for $platform_label..."

# Try new official repo first, then fall back to legacy repo
release_info=""
declare -a release_endpoints=(
    "https://api.github.com/repos/sirius-ms/sirius/releases"
    "https://api.github.com/repos/boecker-lab/sirius/releases"
)

for api_url in "${release_endpoints[@]}"; do
    echo "Querying releases from $api_url ..."
    release_list=$(curl -s -H "Accept: application/vnd.github+json" -H "User-Agent: enpkg-install-script" "$api_url")

    if [ -z "$release_list" ]; then
        echo "Warning: empty response from $api_url" >&2
        continue
    fi

    if ! echo "$release_list" | jq -e 'type == "array"' >/dev/null 2>&1; then
        api_message=$(echo "$release_list" | jq -r '.message // empty' 2>/dev/null)
        if [ -n "$api_message" ]; then
            echo "Warning: GitHub API response from $api_url: $api_message" >&2
            if echo "$api_message" | grep -qi "rate limit"; then
                echo "Hint: export GITHUB_TOKEN=<token> to increase rate limit and retry." >&2
            fi
        else
            echo "Warning: Unexpected response from $api_url" >&2
        fi
        continue
    fi

    release_info=$(echo "$release_list" | jq -rc 'map(select((.draft | not) and (.prerelease | not) and (.assets | length > 0))) | .[0]')

    if [[ -n "$release_info" && "$release_info" != "null" ]]; then
        break
    fi
done

if [[ -z "$release_info" || "$release_info" == "null" ]]; then
    echo "Error: Could not find a non-draft release with downloadable assets in known repositories." >&2
    exit 1
fi

release_tag=$(echo "$release_info" | jq -r '.tag_name // "unknown"')
echo "Using release tag $release_tag."

# Get the download URL for the requested platform zip version, excluding .sha256 files
download_url=$(echo "$release_info" | jq -r --arg pattern "$asset_pattern" '.assets[] | select(.name | test($pattern)) | .browser_download_url' | head -n 1)

if [ -z "$download_url" ]; then
    echo "Error: Could not find a $platform_label zip asset in the latest release."
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

# echo 'Sirius installation file is ready.'

# # Return the path to the Sirius executable

# echo "The path to the Sirius executable is: $(pwd)/sirius/bin"

# # Add additional installation steps if necessary. It might involve moving files to certain directories or setting permissions.


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

# Provide usage hints depending on archive layout
if [[ -d "$install_dir/Contents/MacOS" ]]; then
    mac_bin_dir="$install_dir/Contents/MacOS"
    mac_binary="$mac_bin_dir/sirius"
    echo "Detected macOS application bundle."
    echo "You can start Sirius by running:"
    echo "  \"$mac_binary\""
    echo "Optionally add the binary directory to your PATH:"
    echo "  export PATH=\$PATH:$mac_bin_dir"
elif [[ -d "$install_dir/sirius/bin" ]]; then
    cli_bin_dir="$install_dir/sirius/bin"
    echo "You can start Sirius by running:"
    echo "  \"$cli_bin_dir/sirius\""
    echo "Optionally add the CLI directory to your PATH:"
    echo "  export PATH=\$PATH:$cli_bin_dir"
elif [[ -d "$install_dir/bin" ]]; then
    echo "You can start Sirius by running the binary from $install_dir/bin."
    echo "Consider adding that directory to your PATH."
else
    echo "Sirius files were extracted to $install_dir."
    echo "Please inspect the directory to locate the executable."
fi

echo "For more information on how to use Sirius, please refer to the official documentation."
