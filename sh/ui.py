import os
import sys
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import qrcode
from PIL import Image
from core import SharingCore

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ShareApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Share folder & Files")
        self.resizable(False, False)

        # Dimensions configuration
        self.start_width = 500
        self.start_height = 490
        self.expanded_height = 760
        self.current_height = self.start_height
        self.geometry(f"{self.start_width}x{self.start_height}")

        # State 
        self.selected_path = ""
        self.sharing_type = tk.StringVar(value="folder")
        self.connection_mode = tk.StringVar(value="internet")
        self.generated_url = ""
        self.animation_running = False

        # Initialize the backend engine
        self.core = SharingCore(self)

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        # ── Header ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Share Web Files", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            self, text="Serve files instantly — local or across the internet",
            font=ctk.CTkFont(size=12), text_color="gray"
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
            self, text="Start Sharing",
            fg_color="#377d54", hover_color="#27ae60",
            font=ctk.CTkFont(size=15, weight="bold"), height=44,
            command=self._toggle_sharing,
        )
        self.action_btn.pack(pady=14, padx=30, fill="x")

        # ── Status label ───────────────────────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self, text="", text_color="gray", font=ctk.CTkFont(size=12), wraplength=460
        )
        self.status_label.pack(pady=(0, 4))

        # ── Results frame ──────────────────────────────────────────────────────
        self.result_frame = ctk.CTkFrame(self)
        self.qr_label = ctk.CTkLabel(self.result_frame, text="")
        self.qr_label.pack(pady=(12, 6))

        url_row = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        url_row.pack(padx=16, pady=(0, 12), fill="x")

        self.url_entry = ctk.CTkEntry(url_row, justify="center", state="readonly")
        self.url_entry.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.copy_btn = ctk.CTkButton(url_row, text="Copy", width=72, command=self._copy_link)
        self.copy_btn.pack(side="right")

    # ── Animation Engine ──────────────────────────────────────────────────
    def _animate_window(self, target_height: int):
        if not self.winfo_exists():
            return
            
        step = 16
        delay = 10

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

    # ── Path Selection Mechanics ──────────────────────────────────────────
    def _clear_path(self, _=None):
        self.selected_path = ""
        self.path_label.configure(text="No path selected", text_color="gray", anchor="w")
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

    # ── Controlling Toggles ───────────────────────────────────────────────
    def _toggle_sharing(self):
        if self.core.is_sharing:
            self.core.stop_sharing()
            self._on_sharing_stopped()
        else:
            self.action_btn.configure(text="Starting…", state="disabled")
            self.core.start_sharing(
                self.selected_path, 
                self.sharing_type.get(), 
                self.connection_mode.get()
            )

    def _on_sharing_stopped(self):
        self.action_btn.configure(
            text="Start Sharing", fg_color="#499267", hover_color="#27ae60", state="normal"
        )
        self._lock_inputs(False)
        self._set_status("Sharing stopped.", "gray")
        self._animate_window(self.start_height)

    # ── Core Engine Callback Handlers ─────────────────────────────────────
    def on_status_change(self, text: str, color: str = "gray"):
        self._set_status(text, color)

    def on_error(self, message: str):
        self.action_btn.configure(
            text="Start Sharing", fg_color="#3b7d57", hover_color="#27ae60", state="normal"
        )
        self._lock_inputs(False)
        self._set_status(f"{message}", "#e74c3c")
        self._animate_window(self.start_height)

    def on_sharing_ready(self, url: str):
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

        self.result_frame.pack(pady=8, padx=30, fill="x")
        self.action_btn.configure(
            text="Stop Sharing", fg_color="#e74c3c", hover_color="#c0392b", state="normal"
        )
        self._lock_inputs(True)
        mode = "Local network" if self.connection_mode.get() == "Local Internet" else "Internet (Cloudflare)"
        self._set_status(f"Active — {mode}", "#2ecc71")
        self._animate_window(self.expanded_height)

    # Thread-Safe GUI updates for Background Process calls
    def safe_update_status(self, text: str, color: str = "gray"):
        self.after(0, lambda: self.on_status_change(text, color))

    def safe_error(self, message: str):
        self.after(0, lambda: self.on_error(message))

    def safe_sharing_ready(self, url: str):
        self.after(0, lambda: self.on_sharing_ready(url))

    # ── UI Helpers ────────────────────────────────────────────────────────
    def _set_status(self, text: str, color: str = "gray"):
        self.status_label.configure(text=text, text_color=color)

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
        self.core.stop_sharing()
        self.destroy()
        sys.exit(0)