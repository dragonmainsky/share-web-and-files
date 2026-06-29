import os
import sys
import socket
import re
import threading
import subprocess
import http.server
import socketserver
import urllib.parse
import urllib.request
import shutil
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import qrcode
from PIL import Image

# ── Appearance 
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ── Silent HTTP handler 
class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  


# ── TCP server with SO_REUSEADDR to avoid "port in use" on quick restart ──────
class _ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True  


class ShareApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Share folder & Files")
        self.resizable(False, False)

        # Fix initial dimensions to start height
        self.start_width = 500
        self.start_height = 490
        self.expanded_height = 760
        self.current_height = self.start_height
        self.geometry(f"{self.start_width}x{self.start_height}")

        # ── State ──────────────────────────────────────────────────────────────
        self.selected_path = ""
        self.sharing_type = tk.StringVar(value="folder")
        self.connection_mode = tk.StringVar(value="internet")
        self.is_sharing = False
        self.generated_url = ""
        self.animation_running = False

        # ── Process handles ────────────────────────────────────────────────────
        self.http_server = None
        self.server_port = 0
        self.cf_process = None

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ══════════════════════════════════════════════════════════════════════════
    # UI SETUP
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        # ── Header ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Share Web Files",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="Serve files instantly — local or across the internet",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=(0, 14))

        # ── Step 1 ─────────────────────────────────────────────────────────────
        sel = ctk.CTkFrame(self)
        sel.pack(pady=6, padx=30, fill="x")
        sel.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(sel, text="1 · What to share", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 4), sticky="w"
        )

        segmented_button = ctk.CTkSegmentedButton(
            master=sel,
            variable=self.sharing_type, values=["folder", "Single File"],
            command=self._clear_path
        )

        segmented_button.grid(row=1, column=0, columnspan=2, padx=16, pady=(8, 4), sticky="ew")
        segmented_button.set("folder")

        self._browse_btn = ctk.CTkButton(sel, text="Browse…", command=self._browse_path)
        self._browse_btn.grid(row=2, column=0, columnspan=2, padx=16, pady=(8, 4), sticky="ew")

        self.path_label = ctk.CTkLabel(
            sel, text="No path selected", text_color="gray", wraplength=430, anchor="w"
        )
        self.path_label.grid(row=3, column=0, columnspan=2, padx=16, pady=(2, 10))

        # ── Step 2 ─────────────────────────────────────────────────────────────
        mode = ctk.CTkFrame(self)
        mode.pack(pady=6, padx=30, fill="x")
        mode.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(mode, text="2 · Connection mode", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 4), sticky="w"
        )
        self.mode_segmented_btn = ctk.CTkSegmentedButton(
            master=mode,
            variable=self.connection_mode, 
            values=["internet", "Local Internet"]
        )

        self.mode_segmented_btn.grid(row=1, column=0, padx=16, pady=(4, 12), sticky="ew")
        self.connection_mode.set("internet")

        self._radio_widgets = [segmented_button, self.mode_segmented_btn]

        # ── Action button ──────────────────────────────────────────────────────
        self.action_btn = ctk.CTkButton(
            self,
            text="Start Sharing",
            fg_color="#377d54", hover_color="#27ae60",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self._toggle_sharing,
        )
        self.action_btn.pack(pady=14, padx=30, fill="x")

        # ── Dedicated status label ─────────────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self, text="", text_color="gray",
            font=ctk.CTkFont(size=12), wraplength=460
        )
        self.status_label.pack(pady=(0, 4))

        # ── Results frame (hidden until active) ───────────────────────────────
        self.result_frame = ctk.CTkFrame(self)

        self.qr_label = ctk.CTkLabel(self.result_frame, text="")
        self.qr_label.pack(pady=(12, 6))

        url_row = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        url_row.pack(padx=16, pady=(0, 12), fill="x")

        self.url_entry = ctk.CTkEntry(url_row, justify="center", state="readonly")
        self.url_entry.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.copy_btn = ctk.CTkButton(
            url_row, text="Copy", width=72, command=self._copy_link
        )
        self.copy_btn.pack(side="right")

    # ══════════════════════════════════════════════════════════════════════════
    # SMOOTH ANIMATION ENGINE
    # ══════════════════════════════════════════════════════════════════════════

    def _animate_window(self, target_height: int):
        if not self.winfo_exists():
            return
            
        step = 16  # Pixels moved per frame
        delay = 10  # Milliseconds between frames

        if self.current_height < target_height:
            self.current_height = min(self.current_height + step, target_height)
            self.geometry(f"{self.start_width}x{self.current_height}")
            self.after(delay, lambda: self._animate_window(target_height))
        elif self.current_height > target_height:
            self.current_height = max(self.current_height - step, target_height)
            self.geometry(f"{self.start_width}x{self.current_height}")
            if self.current_height == target_height:
                self.result_frame.pack_forget()
            self.after(delay, lambda: self._animate_window(target_height))
        else:
            self.animation_running = False

    # ══════════════════════════════════════════════════════════════════════════
    # PATH HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _clear_path(self, _=None):
        self.selected_path = ""
        self.path_label.configure(text="No path selected", text_color="gray", anchor="w" )
        self._set_status("")

    def _browse_path(self):
        if self.sharing_type.get() == "folder":
            path = filedialog.askdirectory(title="Select Website / Game Root Folder")
        else:
            path = filedialog.askopenfilename(title="Select File to Share")
        if path:
            self.selected_path = path
            display = os.path.basename(path) if self.sharing_type.get() == "Single File" else path
            self.path_label.configure(text=display, text_color=("black", "white"))
            self._set_status("")

    # ══════════════════════════════════════════════════════════════════════════
    # NETWORK HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _start_local_server(self, serve_dir: str):
        class _DirHandler(_SilentHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=serve_dir, **kwargs)

        self.http_server = _ReuseAddrTCPServer(("0.0.0.0", 0), _DirHandler)
        self.server_port = self.http_server.server_address[1]
        threading.Thread(target=self.http_server.serve_forever, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # SHARING CONTROL
    # ══════════════════════════════════════════════════════════════════════════

    def _toggle_sharing(self):
        if self.is_sharing:
            self._stop_sharing()
        else:
            self._start_sharing()

    def _start_sharing(self):
        if not self.selected_path:
            self._set_status("Please select a file or folder first!", "#e74c3c")
            return

        if not os.path.exists(self.selected_path):
            self._set_status("Selected path no longer exists.", "#e74c3c")
            return

        self.is_sharing = True
        self.action_btn.configure(text="Starting…", state="disabled")
        self._set_status("Launching local server…", "#f1c40f")

        if self.sharing_type.get() == "Single File":
            serve_dir = os.path.dirname(self.selected_path) or "."
            file_name = os.path.basename(self.selected_path)
        else:
            serve_dir = self.selected_path
            file_name = ""

        self._start_local_server(serve_dir)

        if self.connection_mode.get() == "Local Internet":
            local_ip = self._get_local_ip()
            url = f"http://{local_ip}:{self.server_port}"
            if file_name:
                url += f"/{urllib.parse.quote(file_name)}"
            self._display_sharing_data(url)
        else:
            self._set_status("Connecting to Cloudflare… (may take ~10 s)", "#f1c40f")
            threading.Thread(
                target=self._launch_cloudflare_tunnel, args=(file_name,), daemon=True
            ).start()

    def _launch_cloudflare_tunnel(self, file_name: str):
        local_bin = "cloudflared.exe" if os.name == "nt" else "cloudflared"

        if not shutil.which(local_bin) and not os.path.exists(local_bin):
            if os.name == "nt":
                self.after(0, lambda: self._set_status(
                    "Downloading Cloudflare binary… (first run only)", "#f1c40f"
                ))
                try:
                    dl_url = (
                        "https://github.com/cloudflare/cloudflared/releases/latest"
                        "/download/cloudflared-windows-amd64.exe"
                    )
                    urllib.request.urlretrieve(dl_url, local_bin)
                except Exception as e:
                    self.after(0, lambda err=str(e): self._sharing_error(
                        f"Auto-download failed: {err}"
                    ))
                    return
            else:
                self.after(0, lambda: self._sharing_error(
                    "cloudflared not found.\n"
                    "macOS: brew install cloudflared\n"
                    "Linux: sudo apt install cloudflared"
                ))
                return

        executable = local_bin if os.path.exists(local_bin) else "cloudflared"

        try:
            cmd = [
                executable, "tunnel",
                "--loglevel", "info",
                "--url", f"http://127.0.0.1:{self.server_port}",
            ]
            self.cf_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            found_url = []       
            captured_logs = []
            stop = threading.Event()        

            url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

            def _read_stream(stream):
                try:
                    for line in stream:
                        if stop.is_set():
                            break
                        clean = line.strip()
                        if clean:
                            captured_logs.append(clean)
                            if len(captured_logs) > 5:
                                captured_logs.pop(0)
                        match = url_pattern.search(line)
                        if match and not found_url:
                            url = match.group(0)
                            if file_name:
                                url += f"/{urllib.parse.quote(file_name)}"
                            found_url.append(url)
                            stop.set()   
                except Exception:
                    pass
                finally:
                    stop.set()           

            t_err = threading.Thread(target=_read_stream, args=(self.cf_process.stderr,), daemon=True)
            t_out = threading.Thread(target=_read_stream, args=(self.cf_process.stdout,), daemon=True)
            t_err.start()
            t_out.start()

            stop.wait(timeout=45)
            stop.set()   

            if found_url:
                tunnel_url = found_url[0]
                self.after(0, lambda u=tunnel_url: self._display_sharing_data(u))
            else:
                log_summary = " | ".join(captured_logs) or "No log output."
                if len(log_summary) > 160:
                    log_summary = log_summary[:157] + "…"
                self.after(0, lambda lg=log_summary: self._sharing_error(
                    f"Cloudflare tunnel failed.\n{lg}"
                ))

        except FileNotFoundError:
            self.after(0, lambda: self._sharing_error(
                f"Cannot find '{executable}'. Is cloudflared installed and on PATH?"
            ))
        except Exception as e:
            self.after(0, lambda err=str(e): self._sharing_error(f"Unexpected error: {err}"))

    def _stop_sharing(self):
        self.is_sharing = False

        if self.cf_process:
            try:
                self.cf_process.terminate()
            except Exception:
                pass
            self.cf_process = None

        if self.http_server:
            threading.Thread(target=self.http_server.shutdown, daemon=True).start()
            self.http_server = None

        self.action_btn.configure(
            text="Start Sharing",
            fg_color="#499267", hover_color="#27ae60",
            state="normal",
        )
        self._lock_inputs(False)
        self._set_status("Sharing stopped.", "gray")
        
        # Trigger slide-up animation closing the frame
        self._animate_window(self.start_height)

    # ══════════════════════════════════════════════════════════════════════════
    # UI STATE HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _set_status(self, text: str, color: str = "gray"):
        self.status_label.configure(text=text, text_color=color)

    def _display_sharing_data(self, url: str):
        self.generated_url = url

        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        self.url_entry.configure(state="readonly")

        qr = qrcode.QRCode(version=1, box_size=9, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")._img
        
        ctk_img = ctk.CTkImage(light_image=qr_img, dark_image=qr_img, size=(210, 210))
        self.qr_label.configure(image=ctk_img)
        self.qr_label.image = ctk_img  

        # Unpack hidden frame and pack immediately before sliding to render cleanly
        self.result_frame.pack(pady=8, padx=30, fill="x")
        
        self.action_btn.configure(
            text="Stop Sharing",
            fg_color="#e74c3c", hover_color="#c0392b",
            state="normal",
        )
        self._lock_inputs(True)
        mode = "Local network" if self.connection_mode.get() == "Local Internet" else "Internet (Cloudflare)"
        self._set_status(f"Active — {mode}", "#2ecc71")
        
        # Trigger slide-down
        self._animate_window(self.expanded_height)

    def _sharing_error(self, message: str):
        self.is_sharing = False
        if self.cf_process:
            try:
                self.cf_process.terminate()
            except Exception:
                pass
            self.cf_process = None
        if self.http_server:
            threading.Thread(target=self.http_server.shutdown, daemon=True).start()
            self.http_server = None
        
        self.action_btn.configure(
            text="Start Sharing",
            fg_color="#3b7d57", hover_color="#27ae60",
            state="normal",
        )
        self._lock_inputs(False)
        self._set_status(f"{message}", "#e74c3c")
        
        # Collapse back if open during an error
        self._animate_window(self.start_height)

    def _lock_inputs(self, lock: bool):
        state = "disabled" if lock else "normal"
        for w in self._radio_widgets:
            w.configure(state=state)
        self._browse_btn.configure(state=state)

    def _copy_link(self):
        self.clipboard_clear()
        self.clipboard_append(self.generated_url)
        self.copy_btn.configure(text="Copied!", fg_color="#2ecc71")
        self.after(1600, lambda: self.copy_btn.configure(
            text="Copy", fg_color=("#3a7ebf", "#1f538d")
        ))

    def _on_closing(self):
        self._stop_sharing()
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = ShareApp()
    app.mainloop()
