#!/bin/bash

# Function to print messages
say() {
    echo "==> $1"
}

# Update and upgrade system
sudo apt update && sudo apt upgrade -y
say "Updates and upgrades done"

# Install Python and tools
sudo apt install -y python3 python3-pip python3-venv
sleep 5
say "Python3 installed"

# Install Python dependencies from requirements
sudo pip install -r https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/refs/heads/main/requirements.txt
say "Requirements installed"

# Clone the repository
git clone https://github.com/HueyMcSpewy/erm-ce
say "Repo cloned"

# Navigate into the repo
cd erm-ce || exit

# Create empty .env file
touch .env
say ".env file made, remember to fill it out"

# Ask user if they want to install MongoDB
read -p "Do you want to install MongoDB? (y/n): " install_mongo

if [[ "$install_mongo" == "y" || "$install_mongo" == "Y" ]]; then
    sudo apt update
    sudo apt install -y gnupg curl

    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

    sudo apt update
    sudo apt install -y mongodb-org

    sudo systemctl start mongod
    sudo systemctl enable mongod

    say "Install done, MongoDB installed"
else
    say "MongoDB not installed, done"
fi
