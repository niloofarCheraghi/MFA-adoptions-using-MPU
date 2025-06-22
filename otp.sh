#!/bin/bash

# Navigate to the script directory
cd "$(dirname "$0")" || exit 1

# Activate python virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "virtual environment activated\n"
else
    echo "Virtual environment directory 'venv' not found."
    exit 1
fi

# Prompt the user for input
echo "Select an option:"
echo "1- Generate otp"
echo "2- Store secret key"
read -rp "Enter 1 or 2: " choice

case "$choice" in
    1)
        if [ -f "otp.py" ]; then
            python otp.py
        else
            echo "otp.py script not found in the current directory."
            exit 1
        fi
        ;;
    2)
        read -rp "Enter the secret key: " secret_key
        # Save secret_key in JSON format in secret.json
        echo "{\"SECRET_KEY\": \"$secret_key\"}" > secret.json
        echo "Secret key saved to secret.json"
        ;;
    *)
        echo "Invalid selection. Please run the script again and choose 1 or 2."
        exit 1
        ;;
esac