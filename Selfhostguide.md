<p align="center">
  <img src="https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/main/assets/ermlogo.png" alt="ERM CE Logo" width="200"/>
</p>

# ERM CE — Self-Hosting Guide

This guide walks you through **self-hosting ERM CE**, the community edition of the ERM Discord bot, on a **Ubuntu/Debian** server.

**Repository:** [https://github.com/HueyMcSpewy/erm-ce](https://github.com/HueyMcSpewy/erm-ce)

---

## 🛠️ Requirements

- Ubuntu 20.04+ or Debian 11+
- Python 3.9+
- Discord Bot Token
- MongoDB connection URI
- Optional: Sentry URL
- Optional: Bloxlink API Key
- A Linux user with `sudo` privileges

---

## 🚀 Installation

### 1. Download the installer

Use the **raw GitHub URL** to download `install.sh`:

```bash
# Using curl
curl -O https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/main/install.sh

# Or using wget
wget https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/main/install.sh

# Make it executable
chmod +x install.sh
