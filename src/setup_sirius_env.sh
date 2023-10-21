#!/bin/bash

# Script to set environment variables for Sirius

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

# Export the variables
export SIRIUS_USERNAME=$SIRIUS_USERNAME
export SIRIUS_PASSWORD=$SIRIUS_PASSWORD

echo "Environment variables set for session."

# To check the variables, you could use:
# echo "Username: $SIRIUS_USERNAME"
# echo "Password: $SIRIUS_PASSWORD"
