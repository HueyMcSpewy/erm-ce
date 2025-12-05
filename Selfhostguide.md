<p align="center">
  <img src="https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/main/assets/ermlogo.png" alt="ERM CE Logo" width="200"/>
</p>

# ERM CE — Self-Hosting Guide

This guide walks you through **self-hosting ERM CE**, the community edition of the ERM Discord bot, on a **Ubuntu/Debian** server.

**Repository:** [https://github.com/HueyMcSpewy/erm-ce](https://github.com/HueyMcSpewy/erm-ce)

---

## 🛠️ Requirements

- Ubuntu 20.04+ or Debian 11+. **If you're on Windows, you can do this on WSL running Ubuntu**
- Python 3.9+
- Discord Bot Token
- MongoDB connection URI **with username and password**
- Optional: Sentry URL (recommended)
- Optional: Bloxlink API Key (recommended)
- A Linux user with `sudo` privileges

---

## 🚀 Installation
### 1. One-liner that can be run in your terminal
Use this to install ERM CE in one line:
```bash
curl -ssL https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/main/install.sh | bash
```
### 2. Or Download the installer

Use the **raw GitHub URL** to download `install.sh`:

```bash
# Using curl
curl -O https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/main/install.sh

# Or using wget
wget https://raw.githubusercontent.com/HueyMcSpewy/erm-ce/main/install.sh

# Make it executable
chmod +x install.sh
./install.sh
