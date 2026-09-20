# Share Web and Files — Changelog

## v1.2.0 — 2026-09-21

### ✨ New Features
- **Hamburger Menu** — Added a sliding sidebar menu (☰) with smooth open/close animation.
- **Settings Page** — In-app settings panel (no more pop-up windows):
  - **Appearance Mode** — Switch between System, Light, and Dark mode instantly.
  - **Color Theme** — Choose from blue, green, dark-blue, or pick a **custom color** via the built-in color picker.
  - Settings are **saved to `config.json`** and persist across app restarts.
- **About Page** — In-app About panel showing app name and version info.

### 🔧 Improvements
- "Start Sharing" button now follows the selected color theme instead of being hardcoded green.
- All status-reset button colors now use `ThemeManager` for consistency with the active theme.
- Added `config.json` and `custom_theme.json` to `.gitignore` (user-specific files).

### 📁 Files Changed
| File | What changed |
|------|-------------|
| `ui.py` | Added Hamburger Menu, Settings frame, About frame, config load/save, custom theme generator, ThemeManager-based button colors |
| `.gitignore` | Added `config.json` and `custom_theme.json` |

---

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
