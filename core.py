import os
import re
import sys
import socket
import shutil
import threading
import subprocess
import http.server
import socketserver
import urllib.parse
import urllib.request

# ── Silent HTTP handler 
class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  

# ── TCP server with SO_REUSEADDR to avoid "port in use" on quick restart
class _ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True  

class SharingCore:
    def __init__(self, app_interface):
        self.app = app_interface
        self.http_server = None
        self.server_port = 0
        self.cf_process = None
        self.is_sharing = False

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start_local_server(self, serve_dir: str):
        class _DirHandler(_SilentHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=serve_dir, **kwargs)

        self.http_server = _ReuseAddrTCPServer(("0.0.0.0", 0), _DirHandler)
        self.server_port = self.http_server.server_address[1]
        threading.Thread(target=self.http_server.serve_forever, daemon=True).start()

    def start_sharing(self, selected_path, sharing_type: str, connection_mode: str, start_file: str = None, zip_files: bool = True):
        if not selected_path:
            self.app.on_error("Please select a file or folder first!")
            return

        if isinstance(selected_path, (tuple, list)):
            if not all(os.path.exists(p) for p in selected_path):
                self.app.on_error("Some selected files no longer exist.")
                return
        else:
            if not os.path.exists(selected_path):
                self.app.on_error("Selected path no longer exists.")
                return

        self.is_sharing = True
        self.app.on_status_change("Launching local server…", "#f1c40f")

        if sharing_type == "Files":
            if isinstance(selected_path, (tuple, list)) and len(selected_path) > 1:
                if zip_files:
                    self.app.safe_update_status("Zipping files…", "#f1c40f")
                    import tempfile
                    import zipfile
                    
                    temp_dir = tempfile.mkdtemp(prefix="share_")
                    zip_path = os.path.join(temp_dir, "shared_files.zip")
                    
                    try:
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for p in selected_path:
                                zipf.write(p, os.path.basename(p))
                    except Exception as e:
                        self.app.on_error(f"Failed to zip files: {e}")
                        return
                    
                    serve_dir = temp_dir
                    file_name = "shared_files.zip"
                else:
                    self.app.safe_update_status("Preparing files…", "#f1c40f")
                    import tempfile
                    import shutil
                    temp_dir = tempfile.mkdtemp(prefix="share_")
                    try:
                        for p in selected_path:
                            shutil.copy2(p, os.path.join(temp_dir, os.path.basename(p)))
                    except Exception as e:
                        self.app.on_error(f"Failed to copy files: {e}")
                        return
                    serve_dir = temp_dir
                    file_name = ""
            else:
                single_path = selected_path[0] if isinstance(selected_path, (tuple, list)) else selected_path
                serve_dir = os.path.dirname(single_path) or "."
                file_name = os.path.basename(single_path)
        else:
            serve_dir = selected_path
            file_name = start_file if start_file else ""

        self.start_local_server(serve_dir)

        if connection_mode == "Local Internet":  # Matches the UI segment value
            local_ip = self.get_local_ip()
            url = f"http://{local_ip}:{self.server_port}"
            if file_name:
                url += f"/{urllib.parse.quote(file_name)}"
            self.app.on_sharing_ready(url)
        else:
            self.app.on_status_change("Connecting to Cloudflare… (may take ~10 s)", "#f1c40f")
            threading.Thread(
                target=self._launch_cloudflare_tunnel, args=(file_name,), daemon=True
            ).start()

    def _launch_cloudflare_tunnel(self, file_name: str):
        local_bin = "cloudflared.exe" if os.name == "nt" else "cloudflared"

        if not shutil.which(local_bin) and not os.path.exists(local_bin):
            if os.name == "nt":
                self.app.safe_update_status("Downloading Cloudflare binary… (first run only)", "#f1c40f")
                try:
                    dl_url = (
                        "https://github.com/cloudflare/cloudflared/releases/latest"
                        "/download/cloudflared-windows-amd64.exe"
                    )
                    urllib.request.urlretrieve(dl_url, local_bin)
                except Exception as e:
                    self.app.safe_error(f"Auto-download failed: {str(e)}")
                    return
            else:
                self.app.safe_error(
                    "cloudflared not found.\n"
                    "macOS: brew install cloudflared\n"
                    "Linux: sudo apt install cloudflared"
                )
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
                self.app.safe_sharing_ready(found_url[0])
            else:
                log_summary = " | ".join(captured_logs) or "No log output."
                if len(log_summary) > 160:
                    log_summary = log_summary[:157] + "…"
                self.app.safe_error(f"Cloudflare tunnel failed.\n{log_summary}")

        except FileNotFoundError:
            self.app.safe_error(f"Cannot find '{executable}'. Is cloudflared installed and on PATH?")
        except Exception as e:
            self.app.safe_error(f"Unexpected error: {str(e)}")

    def stop_sharing(self):
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