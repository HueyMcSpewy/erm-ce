#!/bin/bash
# ERM CE Auto Installer for Ubuntu/Debian
# Non-root capable & default bot folder: ermCE

set -e

echo "=========================================="
echo "        ERM CE Ubuntu/Debian Installer"
echo "=========================================="
sleep 1

# Ask for bot system username
read -p "Enter the system username to run the bot (will create if doesn't exist): " BOT_USER

# Fixed bot folder name
BOT_FOLDER="ermCE"
INSTALL_PATH="$HOME/$BOT_FOLDER"

# Check if user exists
if id "$BOT_USER" &>/dev/null; then
    echo "User $BOT_USER exists."
else
    echo "User $BOT_USER does not exist."
    read -p "Do you want to create this user? (y/n): " CREATE_USER
    if [[ "$CREATE_USER" =~ ^[Yy]$ ]]; then
        sudo adduser --gecos "" "$BOT_USER"
    else
        echo "User must exist to run the bot. Exiting."
        exit 1
    fi
fi

echo "[1] Updating system..."
sudo apt update -y && sudo apt upgrade -y

echo "[2] Installing dependencies..."
sudo apt install -y python3-full python3-venv python3-pip build-essential \
libffi-dev python3-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev git curl nano screen

echo "[3] Cloning or updating ERM CE repository..."
if [ -d "$INSTALL_PATH" ]; then
    echo "Existing ermCE folder found — pulling latest..."
    cd "$INSTALL_PATH"
    git pull
else
    git clone https://github.com/HueyMcSpewy/erm-ce.git "$INSTALL_PATH"
fi

# Change ownership to BOT_USER
sudo chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_PATH"

echo "[4] Setting up Python virtual environment..."
sudo -u "$BOT_USER" python3 -m venv "$INSTALL_PATH/venv"

echo "[5] Upgrading pip, setuptools, wheel..."
sudo -u "$BOT_USER" "$INSTALL_PATH/venv/bin/pip" install --upgrade pip setuptools wheel

echo "[6] Installing Python dependencies..."
sudo -u "$BOT_USER" "$INSTALL_PATH/venv/bin/pip" install -r "$INSTALL_PATH/requirements.txt"

echo "[7] Configuring .env file interactively..."
ENV_FILE="$INSTALL_PATH/.env"
if [ ! -f "$ENV_FILE" ]; then
    sudo -u "$BOT_USER" cp "$INSTALL_PATH/.env.template" "$ENV_FILE"
fi

read -p "Enter your MongoDB Atlas URI: " MONGO_URI
read -p "Enter your Discord Bot Token: " BOT_TOKEN
read -p "Enter your Custom Guild ID (server ID): " GUILD_ID
read -p "Enter Sentry URL (optional, leave blank if none): " SENTRY_URL
read -p "Enter Bloxlink API Key (optional, leave blank if none): " BLOXLINK_KEY

cat <<EOF >"$ENV_FILE"
MONGO_URL=$MONGO_URI
ENVIRONMENT=PRODUCTION
SENTRY_URL=$SENTRY_URL
PRODUCTION_BOT_TOKEN=$BOT_TOKEN
DEVELOPMENT_BOT_TOKEN=
CUSTOM_GUILD_ID=$GUILD_ID
BLOXLINK_API_KEY=$BLOXLINK_KEY
PANEL_API_URL=
EOF

sudo chown "$BOT_USER":"$BOT_USER" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# Ask if user wants systemd service
read -p "Do you want to setup a systemd service to auto-start the bot? (y/n): " SETUP_SERVICE

if [[ "$SETUP_SERVICE" =~ ^[Yy]$ ]]; then
    SERVICE_NAME="ermCE"
    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

    sudo bash -c "cat <<EOF >$SERVICE_FILE
[Unit]
Description=ERM CE Discord Bot
After=network.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$INSTALL_PATH
ExecStart=$INSTALL_PATH/venv/bin/python3 $INSTALL_PATH/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

    echo "[8] Reloading systemd and enabling service..."
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    echo "Systemd service created. Start it with: sudo systemctl start $SERVICE_NAME"
else
    echo "Skipping systemd service. You can run the bot manually with:"
    echo "sudo -u $BOT_USER $INSTALL_PATH/venv/bin/python3 $INSTALL_PATH/main.py"
    echo "Or use screen/tmux for background running."
fi

echo "=========================================="
echo " ✔ Installation complete!"
echo "Bot installed in: $INSTALL_PATH"
echo "Owner user: $BOT_USER"
echo "Folder name: $BOT_FOLDER"
echo "=========================================="