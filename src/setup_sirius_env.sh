#!/bin/bash

# Script to set and save environment variables for Sirius

# Prompt for the username and password if they are not provided as arguments
if [ -z "$1" ]; then
    read -rp "Enter your Sirius username (email): " SIRIUS_USERNAME
else
    SIRIUS_USERNAME=$1
fi

if [ -z "$2" ]; then
    read -rsp "Enter your Sirius password (input will be hidden): " SIRIUS_PASSWORD
    echo # Newline for better readability after the hidden input
else
    SIRIUS_PASSWORD=$2
fi

# Set the variables
export SIRIUS_USERNAME=$SIRIUS_USERNAME
export SIRIUS_PASSWORD=$SIRIUS_PASSWORD

# Prompt the user to select a shell configuration file
read -rp "Select the shell configuration file (bashrc, zshrc, etc.): " SHELL_CONFIG_FILE

# Check if the user wants to save the variables permanently
read -p "Do you want to save these variables permanently (y/n)? " SAVE_PERMANENTLY

if [[ $SAVE_PERMANENTLY =~ ^[Yy]$ ]]; then
    # Append the variable assignments to the selected shell configuration file
    echo "export SIRIUS_USERNAME=\"$SIRIUS_USERNAME\"" >> "$HOME/.$SHELL_CONFIG_FILE"
    echo "export SIRIUS_PASSWORD=\"$SIRIUS_PASSWORD\"" >> "$HOME/.$SHELL_CONFIG_FILE"
    echo "Variables saved permanently to ~/.$SHELL_CONFIG_FILE."
fi

echo "Environment variables set for session."

# To check the variables, you could use:
# echo "Username: $SIRIUS_USERNAME"
# echo "Password: $SIRIUS_PASSWORD"
