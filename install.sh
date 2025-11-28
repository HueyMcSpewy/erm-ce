#!/bin/bash
# ERM CE Auto Installer for Ubuntu/Debian
# Improved version: cleaner, safer, non-interactive friendly
set -e

echo "=========================================="
echo "        ERM CE Ubuntu/Debian Installer"
echo "=========================================="
sleep 1

# Use ERMCE_USER env if set, otherwise default to current user
BOT_USER="${ERMCE_USER:-$USER}"
echo "→ Bot will run as user: $BOT_USER"

# Bot install path
BOT_FOLDER="ermCE"
INSTALL_PATH="/opt/$BOT_FOLDER"

# Ensure user exists only if ERMCE_USER is set to something else
if ! id "$BOT_USER" &>/dev/null; then
    echo "User $BOT_USER does not exist. Creating..."
    sudo adduser --gecos "" --disabled-password "$BOT_USER"
fi

echo "[1] Updating system..."
sudo apt update -y && sudo apt upgrade -y

echo "[2] Installing dependencies..."
sudo apt install -y python3-full python3-venv python3-pip build-essential \
libffi-dev python3-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev \
libjpeg-dev git curl nano screen

echo "[3] Cloning or updating ERM CE..."
if [ -d "$INSTALL_PATH" ]; then
    echo "→ Existing folder found — pulling latest..."
    sudo git -C "$INSTALL_PATH" pull
else
    sudo git clone https://github.com/HueyMcSpewy/erm-ce.git "$INSTALL_PATH"
fi

# Correct owner
sudo chown -R "$BOT_USER":"$BOT_USER" "$INSTALL_PATH"

echo "[4] Setting up virtualenv..."
sudo -u "$BOT_USER" python3 -m venv "$INSTALL_PATH/venv"

echo "[5] Upgrading pip..."
sudo -u "$BOT_USER" "$INSTALL_PATH/venv/bin/pip" install -U pip setuptools wheel

echo "[6] Installing Python requirements..."
sudo -u "$BOT_USER" "$INSTALL_PATH/venv/bin/pip" install -r "$INSTALL_PATH/requirements.txt"

# --- ENV SETUP ---
ENV_FILE="$INSTALL_PATH/.env"
TEMPLATE="$INSTALL_PATH/.env.template"

echo "[7] Creating .env file..."
if [ ! -f "$ENV_FILE" ]; then
    sudo -u "$BOT_USER" cp "$TEMPLATE" "$ENV_FILE"
fi

# Interactive input
read -p "MongoDB URI: " MONGO_URI
read -p "Bot Token: " BOT_TOKEN
read -p "Guild ID: " GUILD_ID
read -p "Sentry URL (optional): " SENTRY_URL
read -p "Bloxlink API Key (optional): " BLOXLINK_KEY

sudo bash -c "cat <<EOF > $ENV_FILE
MONGO_URL=$MONGO_URI
ENVIRONMENT=PRODUCTION
SENTRY_URL=$SENTRY_URL
PRODUCTION_BOT_TOKEN=$BOT_TOKEN
DEVELOPMENT_BOT_TOKEN=
CUSTOM_GUILD_ID=$GUILD_ID
BLOXLINK_API_KEY=$BLOXLINK_KEY
PANEL_API_URL=
EOF"

sudo chown "$BOT_USER":"$BOT_USER" "$ENV_FILE"
sudo chmod 600 "$ENV_FILE"

echo
read -p "Setup systemd service? (y/n): " SETUP_SERVICE

if [[ "$SETUP_SERVICE" =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/ermCE.service"

    echo "[8] Creating systemd service..."
    sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=ERM CE Discord Bot
After=network.target

[Service]
User=$BOT_USER
WorkingDirectory=$INSTALL_PATH
ExecStart=$INSTALL_PATH/venv/bin/python3 $INSTALL_PATH/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

    sudo systemctl daemon-reload
    sudo systemctl enable ermCE
    echo "→ Start with: sudo systemctl start ermCE"
else
    echo "Skipping systemd service."
fi

echo "=========================================="
echo " ✔ Installation complete!"
echo "Installed in: $INSTALL_PATH"
echo "Running user: $BOT_USER"
echo "=========================================="
