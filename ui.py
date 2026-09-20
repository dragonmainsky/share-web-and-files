import os
import sys
import json
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import qrcode
from PIL import Image
from core import SharingCore

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"appearance_mode": "System", "color_theme": "blue"}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
    except:
        pass

def create_custom_theme(hex_color: str):
    theme_path = os.path.join(os.path.dirname(ctk.__file__), "assets", "themes", "blue.json")
    try:
        with open(theme_path, "r") as f:
            theme_data = f.read()
    except Exception:
        return None

    # Calculate hover color (slightly darker)
    hc = hex_color.lstrip('#')
    try:
        r, g, b = tuple(int(hc[i:i+2], 16) for i in (0, 2, 4))
        hover_hex = f"#{max(0, r-30):02x}{max(0, g-30):02x}{max(0, b-30):02x}"
    except:
        hover_hex = hex_color

    theme_data = theme_data.replace("#3B8ED0", hex_color).replace("#1F6AA5", hex_color)
    theme_data = theme_data.replace("#36719F", hover_hex).replace("#144870", hover_hex)
    
    custom_path = os.path.abspath("custom_theme.json")
    try:
        with open(custom_path, "w") as f:
            f.write(theme_data)
        return custom_path
    except:
        return None

app_config = load_config()
ctk.set_appearance_mode(app_config.get("appearance_mode", "System"))

_theme = app_config.get("color_theme", "blue")
if _theme == "custom" and os.path.exists("custom_theme.json"):
    try:
        ctk.set_default_color_theme(os.path.abspath("custom_theme.json"))
    except:
        ctk.set_default_color_theme("blue")
else:
    try:
        ctk.set_default_color_theme(_theme)
    except:
        ctk.set_default_color_theme("blue")

class ShareApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Share folder & Files")
        self.resizable(False, False)

        # Dimensions configuration
        self.start_width = 500
        self.start_height = 550
        self.expanded_height = 820
        self.current_height = self.start_height
        self.geometry(f"{self.start_width}x{self.start_height}")

        # State 
        self.selected_path = ""
        self.sharing_type = tk.StringVar(value="Folder")
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
            variable=self.sharing_type, values=["Folder", "Files"],
            command=self._clear_path
        )
        segmented_button.grid(row=1, column=0, columnspan=2, padx=16, pady=(8, 4), sticky="ew")
        segmented_button.set("Folder")

        self._browse_btn = ctk.CTkButton(sel, text="Browse…", command=self._browse_path)
        self._browse_btn.grid(row=2, column=0, columnspan=2, padx=16, pady=(8, 4), sticky="ew")

        self.path_label = ctk.CTkLabel(
            sel, text="No path selected", text_color="gray", wraplength=430, anchor="w"
        )
        self.path_label.grid(row=3, column=0, columnspan=2, padx=16, pady=(2, 10))

        self.start_file_label = ctk.CTkLabel(sel, text="Start file (optional, e.g. index.html):", text_color="gray", anchor="w")
        self.start_file_label.grid(row=4, column=0, columnspan=2, padx=16, pady=(0, 2), sticky="w")
        
        self.start_file_entry = ctk.CTkEntry(sel, placeholder_text="index.html")
        self.start_file_entry.grid(row=5, column=0, padx=(16, 8), pady=(0, 10), sticky="ew")
        
        self.start_file_browse_btn = ctk.CTkButton(sel, text="Browse File…", width=90, command=self._browse_start_file)
        self.start_file_browse_btn.grid(row=5, column=1, padx=(0, 16), pady=(0, 10), sticky="e")

        self.zip_option_var = tk.BooleanVar(value=True)
        self.zip_checkbox = ctk.CTkCheckBox(sel, text="Zip files before sharing", variable=self.zip_option_var)
        # We will grid this dynamically in _browse_path


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

        # Initialize visibility
        self._clear_path()
        
        # Hamburger Menu
        self._setup_hamburger_menu()

    def _setup_hamburger_menu(self):
        self.menu_open = False
        self.menu_width = 200
        self.closed_x = -200
        self.current_x = self.closed_x

        # Sidebar with fixed width, relheight to fill vertically
        self.sidebar = ctk.CTkFrame(self, width=self.menu_width, corner_radius=0)
        self.sidebar.place(x=self.current_x, y=0, relheight=1)

        # Hamburger button on the main window
        self.hamburger_btn = ctk.CTkButton(
            self, text="☰", width=40, height=40,
            command=self._toggle_menu, font=("Arial", 20),
            fg_color="transparent", text_color=("black", "white"), hover_color=("gray80", "gray30")
        )
        self.hamburger_btn.place(x=10, y=10)

        # Close button inside the sidebar
        self.close_menu_btn = ctk.CTkButton(
            self.sidebar, text="✕", width=40, height=40,
            command=self._toggle_menu, font=("Arial", 20),
            fg_color="transparent", text_color=("black", "white"), hover_color=("gray80", "gray30")
        )
        self.close_menu_btn.place(x=150, y=10)

        # Menu Label
        self.menu_label = ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial", 20, "bold"))
        
        # Menu buttons with commands
        self.menu_buttons = []
        
        self.settings_btn = ctk.CTkButton(self.sidebar, text="Settings", width=160, command=self._open_settings)
        self.menu_buttons.append((self.settings_btn, 120))
        
        self.about_btn = ctk.CTkButton(self.sidebar, text="About", width=160, command=self._open_about)
        self.menu_buttons.append((self.about_btn, 170))

        # Setup the settings frame overlay
        self._setup_settings_frame()
        self._setup_about_frame()

    def _setup_settings_frame(self):
        # Settings Frame overlay (hidden by default)
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0)
        
        # Back button
        back_btn = ctk.CTkButton(
            self.settings_frame, text="← Back", width=60, fg_color="transparent", 
            text_color=("black", "white"), hover_color=("gray80", "gray30"),
            command=self._close_settings
        )
        back_btn.place(x=10, y=10)

        # Title
        ctk.CTkLabel(self.settings_frame, text="Settings", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 20))

        # Appearance Mode
        ctk.CTkLabel(self.settings_frame, text="Appearance Mode", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.settings_frame, values=["System", "Light", "Dark"],
            command=self._change_appearance_mode
        )
        self.appearance_mode_optionemenu.pack(pady=5)
        self.appearance_mode_optionemenu.set(app_config.get("appearance_mode", "System"))

        # Color Theme
        ctk.CTkLabel(self.settings_frame, text="Color Theme", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.theme_optionemenu = ctk.CTkOptionMenu(
            self.settings_frame, values=["blue", "green", "dark-blue", "custom..."],
            command=self._change_color_theme
        )
        self.theme_optionemenu.pack(pady=5)
        
        current_theme = app_config.get("color_theme", "blue")
        self.theme_optionemenu.set("custom..." if current_theme == "custom" else current_theme)

        # Restart notice (hidden by default)
        self.theme_restart_label = ctk.CTkLabel(
            self.settings_frame, text="* Restart app to apply color theme", 
            text_color="#e74c3c", font=ctk.CTkFont(size=11)
        )

    def _open_settings(self):
        self._toggle_menu() # close the sidebar
        # Show settings frame covering the whole window
        self.settings_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.settings_frame.tkraise()

    def _close_settings(self):
        self.settings_frame.place_forget()

    def _change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        app_config["appearance_mode"] = new_mode
        save_config(app_config)

    def _change_color_theme(self, new_theme: str):
        if new_theme == "custom...":
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Choose Custom Theme Color")
            if color and color[1]:
                create_custom_theme(color[1])
                app_config["color_theme"] = "custom"
                app_config["custom_color"] = color[1]
                save_config(app_config)
                self.theme_restart_label.pack(pady=(0, 5))
            else:
                # Cancelled, revert to old value
                old_theme = app_config.get("color_theme", "blue")
                self.theme_optionemenu.set("custom..." if old_theme == "custom" else old_theme)
        else:
            app_config["color_theme"] = new_theme
            save_config(app_config)
            self.theme_restart_label.pack(pady=(0, 5))

    def _setup_about_frame(self):
        self.about_frame = ctk.CTkFrame(self, corner_radius=0)
        
        # Back button
        back_btn = ctk.CTkButton(
            self.about_frame, text="← Back", width=60, fg_color="transparent", 
            text_color=("black", "white"), hover_color=("gray80", "gray30"),
            command=self._close_about
        )
        back_btn.place(x=10, y=10)

        ctk.CTkLabel(self.about_frame, text="Share Web Files", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(50, 10))
        ctk.CTkLabel(self.about_frame, text="Version: 1.2.0\n\nA simple tool to share folders\nand files over LAN or Internet.", justify="center", font=ctk.CTkFont(size=14)).pack()

    def _open_about(self):
        self._toggle_menu()
        self.about_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.about_frame.tkraise()

    def _close_about(self):
        self.about_frame.place_forget()

    def _toggle_menu(self):
        self.menu_open = not self.menu_open
        
        if self.menu_open:
            self.menu_label.place(x=20, y=70)
            for btn, target_y in self.menu_buttons:
                btn.place(x=20, y=target_y)
            self.sidebar.lift()
        else:
            self.menu_label.place_forget()
            for btn, _ in self.menu_buttons:
                btn.place_forget()

        self._animate_menu()

    def _animate_menu(self):
        target = 0 if self.menu_open else self.closed_x
        diff = target - self.current_x
        
        if abs(diff) > 1:
            self.current_x += diff * 0.3
            self.sidebar.place(x=int(self.current_x), y=0, relheight=1)
            self.after(10, self._animate_menu)
        else:
            self.current_x = target
            self.sidebar.place(x=target, y=0, relheight=1)

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
        if hasattr(self, 'zip_checkbox'):
            self.zip_checkbox.grid_remove()
            
        if self.sharing_type.get() == "Folder":
            self.start_file_label.grid()
            self.start_file_entry.grid()
            self.start_file_browse_btn.grid()
        else:
            self.start_file_label.grid_remove()
            self.start_file_entry.grid_remove()
            self.start_file_browse_btn.grid_remove()

    def _browse_start_file(self):
        initial_dir = self.selected_path if self.selected_path else "/"
        file_path = filedialog.askopenfilename(
            title="Select Start File",
            initialdir=initial_dir
        )
        if file_path:
            if self.selected_path and file_path.startswith(self.selected_path):
                rel_path = os.path.relpath(file_path, self.selected_path)
                rel_path = rel_path.replace("\\", "/")
                self.start_file_entry.delete(0, tk.END)
                self.start_file_entry.insert(0, rel_path)
            else:
                self.start_file_entry.delete(0, tk.END)
                self.start_file_entry.insert(0, os.path.basename(file_path))

    def _browse_path(self):
        if self.sharing_type.get() == "Folder":
            path = filedialog.askdirectory(title="Select Website / Game Root Folder")
        else:
            path = filedialog.askopenfilenames(title="Select Files to Share")
        
        if path:
            self.selected_path = path
            if hasattr(self, 'zip_checkbox'):
                self.zip_checkbox.grid_remove()

            if self.sharing_type.get() == "Files":
                display = f"{len(path)} files selected" if isinstance(path, tuple) else os.path.basename(path)
                if isinstance(path, tuple) and len(path) > 1:
                    self.zip_option_var.set(True)
                    self.zip_checkbox.grid(row=6, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="w")
            else:
                display = path
            self.path_label.configure(text=display, text_color=("black", "white"))
            self._set_status("")

    # ── Controlling Toggles ───────────────────────────────────────────────
    def _toggle_sharing(self):
        if self.core.is_sharing:
            self.core.stop_sharing()
            self._on_sharing_stopped()
        else:
            self.action_btn.configure(text="Starting…", state="disabled")
            start_file = self.start_file_entry.get().strip() if hasattr(self, 'start_file_entry') and self.sharing_type.get() == "Folder" else None
            
            # Get zip option
            zip_files = self.zip_option_var.get() if hasattr(self, 'zip_option_var') else True

            self.core.start_sharing(
                self.selected_path, 
                self.sharing_type.get(), 
                self.connection_mode.get(),
                start_file=start_file,
                zip_files=zip_files
            )

    def _on_sharing_stopped(self):
        primary_fg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        primary_hover = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
        self.action_btn.configure(
            text="Start Sharing", fg_color=primary_fg, hover_color=primary_hover, state="normal"
        )
        self._lock_inputs(False)
        self._set_status("Sharing stopped.", "gray")
        self._animate_window(self.start_height)

    # ── Core Engine Callback Handlers ─────────────────────────────────────
    def on_status_change(self, text: str, color: str = "gray"):
        self._set_status(text, color)

    def on_error(self, message: str):
        primary_fg = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        primary_hover = ctk.ThemeManager.theme["CTkButton"]["hover_color"]
        self.action_btn.configure(
            text="Start Sharing", fg_color=primary_fg, hover_color=primary_hover, state="normal"
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
        if hasattr(self, 'start_file_entry'):
            self.start_file_entry.configure(state=state)
        if hasattr(self, 'start_file_browse_btn'):
            self.start_file_browse_btn.configure(state=state)

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