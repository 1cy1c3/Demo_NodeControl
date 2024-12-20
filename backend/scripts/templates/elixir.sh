#!/bin/bash

# Update and install dependencies
echo "Updating system and installing dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io curl -y

# Set Variables
# shellcheck disable=SC1083
STRATEGY_EXECUTOR_IP_ADDRESS={ip}
# shellcheck disable=SC1083
STRATEGY_EXECUTOR_DISPLAY_NAME={name}
# shellcheck disable=SC1083
STRATEGY_EXECUTOR_BENEFICIARY={wallet}
# shellcheck disable=SC1083
SIGNER_PRIVATE_KEY={priv_key}

# URL to download the file
FILE_URL="https://files.elixir.finance/validator.env"


# Download the file
echo "Downloading the file..."
curl -O $FILE_URL

# Create a backup of the original file (optional but recommended)
echo "Creating a backup of the original file..."
cp validator.env validator.env.bak

# Replace the variables in the file
echo "Updating the file with provided variables..."
sed -i "s|STRATEGY_EXECUTOR_IP_ADDRESS=.*|STRATEGY_EXECUTOR_IP_ADDRESS=${STRATEGY_EXECUTOR_IP_ADDRESS}|g" validator.env
sed -i "s|STRATEGY_EXECUTOR_DISPLAY_NAME=.*|STRATEGY_EXECUTOR_DISPLAY_NAME=${STRATEGY_EXECUTOR_DISPLAY_NAME}|g" validator.env
sed -i "s|STRATEGY_EXECUTOR_BENEFICIARY=.*|STRATEGY_EXECUTOR_BENEFICIARY=${STRATEGY_EXECUTOR_BENEFICIARY}|g" validator.env
sed -i "s|SIGNER_PRIVATE_KEY=.*|SIGNER_PRIVATE_KEY=${SIGNER_PRIVATE_KEY}|g" validator.env

echo "File updated successfully!"

# Start Docker container
echo "Starting Docker container..."
sudo docker run -d --env-file validator.env --name elixir --restart unless-stopped elixirprotocol/validator:v3

echo "Docker container started successfully!"

# sudo docker logs -f elixir