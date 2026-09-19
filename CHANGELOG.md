# Share Web and Files — Changelog

## v1.1.0 — 2026-09-19

### ✨ New Features
- **Browse Start File button** — Added a "Browse File…" button next to the start file input.  
  Now you can pick your starting file (e.g. `index.html`) directly from the selected folder instead of typing the name manually.
- **Zip before sharing** — When you select **more than 1 file** in Files mode, a  
  **"Zip files before sharing"** checkbox appears automatically (checked by default).  
  - ✅ Checked → all files are compressed into `shared_files.zip` and shared as a single download.  
  - ☐ Unchecked → files are served as a directory listing so the receiver can pick individual files.

### 🔧 Improvements
- Start file entry and browse button are properly disabled/enabled when sharing starts/stops.
- Zip checkbox is hidden when switching back to Folder mode or clearing the path.

### 📁 Files Changed
| File | What changed |
|------|-------------|
| `ui.py` | Added Browse File button, Zip checkbox, updated `_clear_path`, `_browse_path`, `_lock_inputs` |
| `core.py` | Added `zip_files` parameter, conditional zip vs raw file serving logic |

---

## v1.0.0 — 2026-09-19

### 🎉 Initial Release
- Share a folder or individual files over LAN or the internet.
- Local sharing via built-in HTTP server.
- Internet sharing via temporary Cloudflare Tunnel URL.
- QR code generation for easy mobile access.
- Auto-download of `cloudflared.exe` on first use (Windows).
- Copy link button.
