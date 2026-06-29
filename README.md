# Share Web Files

A small desktop app for sharing a folder or single file over your local network, with optional internet sharing through Cloudflare Tunnel.

## Features

- Pick a folder or a single file to share.
- Share over the local network.
- Share over the internet with a temporary Cloudflare Tunnel URL.
- Generate a QR code for the sharing link.

## Requirements

- Python 3.10 or newer
- Tkinter, usually included with Python on Windows
- Python packages listed in `requirements.txt`
- Optional: `cloudflared` for internet sharing

On Windows, the app can download `cloudflared.exe` automatically on first use. If you prefer installing it manually, download it from Cloudflare's official documentation:

https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/

## Installation

Clone the repository, then install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python app.py
```

## Notes

- The app starts a temporary local HTTP server while sharing is active.
- Internet sharing uses a temporary `trycloudflare.com` URL.
- Stop sharing from the app before closing it.
