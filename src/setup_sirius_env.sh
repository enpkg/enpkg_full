#!/bin/bash

# Script to set and save environment variables for Sirius

# Prompt for the username and password if they are not provided as arguments
if [ -z "$1" ]; then
    read -rp "Enter your Sirius username (email): " SIRIUS_USERNAME
else
    SIRIUS_USERNAME=$1
fi

if [ -z "$2" ]; then
    while true; do
        read -rsp "Enter your Sirius password (input will be hidden): " SIRIUS_PASSWORD
        if [ -z "$SIRIUS_PASSWORD" ]; then
            echo "Password cannot be empty. Please try again."
        else
            echo # Newline for better readability after the hidden input
            break
        fi
    done
else
    SIRIUS_PASSWORD=$2
fi

# Set the variables
export SIRIUS_USERNAME=$SIRIUS_USERNAME
export SIRIUS_PASSWORD=$SIRIUS_PASSWORD

# Default shell configuration file
SHELL_CONFIG_FILE=".bashrc"

# Prompt the user to select a shell configuration file
read -rp "Select the shell configuration file (default is $SHELL_CONFIG_FILE): " USER_SHELL_CONFIG_FILE
SHELL_CONFIG_FILE=${USER_SHELL_CONFIG_FILE:-$SHELL_CONFIG_FILE}

# Check if the selected shell configuration file exists and is writable
if [ ! -w "$HOME/$SHELL_CONFIG_FILE" ]; then
    echo "Error: $HOME/$SHELL_CONFIG_FILE is not writable or does not exist."
    exit 1
fi

# Prompt the user to save the variables permanently
read -p "Do you want to save these variables permanently (y/n)? " SAVE_PERMANENTLY

if [[ $SAVE_PERMANENTLY =~ ^[Yy]$ ]]; then
    # Append the variable assignments to the selected shell configuration file
    echo "export SIRIUS_USERNAME=\"$SIRIUS_USERNAME\"" >> "$HOME/$SHELL_CONFIG_FILE"
    echo "export SIRIUS_PASSWORD=\"$SIRIUS_PASSWORD\"" >> "$HOME/$SHELL_CONFIG_FILE"
    echo "Variables saved permanently to ~/.$SHELL_CONFIG_FILE."
fi

echo "Environment variables set for session."
