#!/usr/bin/env python3
"""
MyCraft Launcher
Unified entry point for players and content creators.
"""

# TODO: Tag for refactoring; length

# === DEPENDENCY CHECK (before importing engine code) ===
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import panda3d
        return True, None
    except ImportError:
        return False, "panda3d"

def find_venv():
    """Try to find a venv in common locations."""
    possible_venvs = [
        Path("venv/bin/python3"),
        Path("venv/bin/python"),
        Path(".venv/bin/python3"),
        Path(".venv/bin/python"),
    ]
    
    for venv_path in possible_venvs:
        if venv_path.exists():
            return str(venv_path.absolute())
    return None

# Check dependencies before doing anything else
deps_ok, missing_dep = check_dependencies()
if not deps_ok:
    print("=" * 70)
    print("⚠️  MyCraft Launcher - Missing Dependencies")
    print("=" * 70)
    print()
    print(f"Missing: {missing_dep}")
    print()
    
    # Try to find venv
    venv_python = find_venv()
    if venv_python:
        print("✓ Found virtual environment!")
        print()
        print("Please run the launcher using:")
        print(f"  {venv_python} launcher.py")
        print()
        print("Or activate the venv first:")
        print("  source venv/bin/activate")
        print("  ./launcher.py")
    else:
        print("Please install dependencies:")
        print()
        print("Option 1 - Use virtual environment (recommended):")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate")
        print("  pip install -r requirements.txt")
        print("  ./launcher.py")
        print()
        print("Option 2 - Install system-wide:")
        print("  pip install -r requirements.txt")
        print("  ./launcher.py")
    
    print()
    print("=" * 70)
    input("Press Enter to exit...")
    sys.exit(1)

# === IMPORTS (only after dependency check passes) ===
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import socket
import time
import threading
import json
from engine.networking.discovery import find_servers


class FirstLaunchWizard:
    """Dialog shown on first launch to ask user intent."""
    
    def __init__(self, parent):
        self.result = None  # 'play' or 'create'
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Welcome to MyCraft!")
        self.dialog.geometry("500x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 500) // 2
        y = (self.dialog.winfo_screenheight() - 350) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self._build_ui()
        
    def _build_ui(self):
        # Header
        header = tk.Frame(self.dialog, bg="#2c3e50", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header, 
            text="🎮 Welcome to MyCraft!", 
            font=("Helvetica", 22, "bold"), 
            bg="#2c3e50", 
            fg="white"
        ).pack(pady=25)
        
        # Content
        content = ttk.Frame(self.dialog, padding="30")
        content.pack(fill="both", expand=True)
        
        tk.Label(
            content,
            text="What would you like to do?",
            font=("Helvetica", 14),
            fg="#34495e"
        ).pack(pady=(0, 25))
        
        # Play button
        play_frame = ttk.Frame(content)
        play_frame.pack(fill="x", pady=8)
        
        play_btn = tk.Button(
            play_frame,
            text="🎮  PLAY THE GAME",
            font=("Helvetica", 14, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#2ecc71",
            activeforeground="white",
            cursor="hand2",
            command=self._select_play,
            height=2
        )
        play_btn.pack(fill="x")
        
        tk.Label(
            play_frame,
            text="Explore worlds, battle enemies, play with friends",
            font=("Helvetica", 10),
            fg="#7f8c8d"
        ).pack(pady=(5, 0))
        
        # Create button
        create_frame = ttk.Frame(content)
        create_frame.pack(fill="x", pady=8)
        
        create_btn = tk.Button(
            create_frame,
            text="🎨  CREATE CONTENT",
            font=("Helvetica", 14, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#5dade2",
            activeforeground="white",
            cursor="hand2",
            command=self._select_create,
            height=2
        )
        create_btn.pack(fill="x")
        
        tk.Label(
            create_frame,
            text="Design characters, create animations, build assets",
            font=("Helvetica", 10),
            fg="#7f8c8d"
        ).pack(pady=(5, 0))
        
    def _select_play(self):
        self.result = "play"
        self.dialog.destroy()
        
    def _select_create(self):
        self.result = "create"
        self.dialog.destroy()
        
    def show(self):
        """Show dialog and wait for user choice."""
        self.dialog.wait_window()
        return self.result


class MyCraftLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("MyCraft Launcher")
        self.root.geometry("800x750")
        self.root.resizable(True, True)
        
        # Settings file path
        self.settings_file = Path.home() / ".mycraft_prefs.json"
        self.settings = self.load_settings()
        
        # Internal state
        self.discovered_servers = []
        self.advanced_visible = False
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("Action.TButton", font=("Helvetica", 12, "bold"))
        style.configure("Host.TButton", font=("Helvetica", 12, "bold"), foreground="white", background="#27ae60")
        style.map("Host.TButton", background=[('active', '#2ecc71')])
        style.configure("Small.TButton", font=("Helvetica", 9))
        style.configure("Editor.TButton", font=("Helvetica", 11, "bold"))
        
        # Header
        self._build_header()
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create tabs
        self.play_tab = ttk.Frame(self.notebook, padding="10")
        self.create_tab = ttk.Frame(self.notebook, padding="10")
        self.advanced_tab = ttk.Frame(self.notebook, padding="10")
        
        self.notebook.add(self.play_tab, text="  🎮 PLAY  ")
        self.notebook.add(self.create_tab, text="  🎨 CREATE  ")
        self.notebook.add(self.advanced_tab, text="  ⚙️ ADVANCED  ")
        
        # Build tab contents
        self._build_play_tab()
        self._build_create_tab()
        self._build_advanced_tab()
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Helvetica", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Background Monitoring
        self._update_server_status()
        self.refresh_servers()
        
        # Check for first launch
        if not self.settings.get("has_launched_before", False):
            self.root.after(100, self._show_first_launch_wizard)
            
    def _build_header(self):
        """Build the header bar."""
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=90)
        header_frame.pack(fill="x")
        
        title_frame = tk.Frame(header_frame, bg="#2c3e50")
        title_frame.pack(pady=(15, 5))
        
        tk.Label(title_frame, text="MyCraft", font=("Helvetica", 28, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        tk.Label(title_frame, text=" v0.5", font=("Helvetica", 14), bg="#2c3e50", fg="#95a5a6").pack(side=tk.LEFT, pady=(10, 0))
        
        # Show Local IP
        self.local_ip = self._get_local_ip()
        ip_label = tk.Label(header_frame, text=f"Your LAN IP: {self.local_ip}", font=("Helvetica", 12), bg="#2c3e50", fg="#bdc3c7")
        ip_label.pack(pady=(0, 15))
        
    def _build_play_tab(self):
        """Build the PLAY tab for players."""
        # Two-Column Layout
        left_col = ttk.LabelFrame(self.play_tab, text=" Quick Play ", padding="15")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        right_col = ttk.LabelFrame(self.play_tab, text=" Multiplayer ", padding="15")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.play_tab.columnconfigure(0, weight=1)
        self.play_tab.columnconfigure(1, weight=1)
        
        # --- Left Column: Quick Play ---
        ttk.Label(left_col, text="Jump right into the game!\nNo setup needed.", 
                  justify=tk.CENTER, foreground="#7f8c8d").pack(pady=(0, 20))
        
        # Player Name
        ttk.Label(left_col, text="Your Name:").pack(anchor="w", pady=(0, 2))
        self.name_entry = ttk.Entry(left_col, width=30)
        self.name_entry.insert(0, self.settings.get("player_name", "Player"))
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Presets
        ttk.Label(left_col, text="Play Style:").pack(anchor="w", pady=(0, 2))
        self.preset_var = tk.StringVar(value=self.settings.get("preset", "creative"))
        preset_combo = ttk.Combobox(left_col, textvariable=self.preset_var, state="readonly")
        preset_combo['values'] = ('creative', 'testing', 'performance')
        preset_combo.pack(fill="x", pady=(0, 5))
        preset_combo.bind('<<ComboboxSelected>>', self.update_preset_desc)
        
        self.preset_desc = tk.Label(left_col, text="", font=("Helvetica", 9), fg="#7f8c8d", anchor="w", justify=tk.LEFT)
        self.preset_desc.pack(fill="x", pady=(0, 20))
        self.update_preset_desc()
        
        # Single Player Button
        self.single_btn = ttk.Button(left_col, text="🎮 PLAY NOW", command=self.launch_single_player, style="Action.TButton")
        self.single_btn.pack(fill="x", pady=5, ipady=15)
        
        # --- Right Column: Multiplayer ---
        ttk.Label(right_col, text="Join friends on your network.", 
                  justify=tk.CENTER, foreground="#7f8c8d").pack(pady=(0, 15))
        
        # Server IP
        ttk.Label(right_col, text="Server Address:").pack(anchor="w", pady=(0, 2))
        self.host_entry = ttk.Entry(right_col, width=30)
        self.host_entry.insert(0, self.settings.get("server_host", "localhost"))
        self.host_entry.pack(fill="x", pady=(0, 10))
        
        self.join_btn = ttk.Button(right_col, text="🌐 JOIN LAN SERVER", command=self.launch_multiplayer, style="Action.TButton")
        self.join_btn.pack(fill="x", pady=5, ipady=8)
        
        # Server Discovery
        discovery_frame = ttk.Frame(right_col)
        discovery_frame.pack(fill="x", pady=(15, 5))
        
        ttk.Label(discovery_frame, text="Found Servers:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.refresh_btn = ttk.Button(discovery_frame, text="🔄 Refresh", command=self.refresh_servers, width=10)
        self.refresh_btn.pack(side=tk.RIGHT)
        
        self.server_list = tk.Listbox(right_col, height=4, font=("Courier", 10))
        self.server_list.pack(fill="x", pady=(0, 10))
        self.server_list.bind('<<ListboxSelect>>', self.on_server_select)
        
        # Advanced Settings Toggle
        self.adv_btn = ttk.Button(right_col, text="⚙️ More Options ▼", command=self.toggle_advanced_options, style="Small.TButton")
        self.adv_btn.pack(fill="x", pady=(5, 0))
        
        # Advanced Options Frame (Hidden by default)
        self.adv_frame = ttk.Frame(right_col)
        
        # Sensitivity
        ttk.Label(self.adv_frame, text="Sensitivity:").pack(anchor="w", pady=(5, 0))
        self.sens_var = tk.DoubleVar(value=self.settings.get("sensitivity", 40.0))
        sens_scale = ttk.Scale(self.adv_frame, from_=10, to=100, variable=self.sens_var, command=lambda v: self.sens_label.config(text=f"{int(float(v))}"))
        sens_scale.pack(fill="x")
        self.sens_label = ttk.Label(self.adv_frame, text=f"{int(self.sens_var.get())}")
        self.sens_label.pack(anchor="e")
        
        # FOV
        ttk.Label(self.adv_frame, text="FOV:").pack(anchor="w", pady=(5, 0))
        self.fov_var = tk.IntVar(value=self.settings.get("fov", 90))
        fov_combo = ttk.Combobox(self.adv_frame, textvariable=self.fov_var, state="readonly", values=(60, 75, 90, 100, 110, 120))
        fov_combo.pack(fill="x")
        
        # Checkboxes
        self.use_config_var = tk.BooleanVar(value=self.settings.get("use_config", True))
        ttk.Checkbutton(self.adv_frame, text="Hot-Reload Config", variable=self.use_config_var).pack(anchor="w", pady=(10, 2))

        self.record_var = tk.BooleanVar(value=self.settings.get("record_session", False))
        ttk.Checkbutton(self.adv_frame, text="Record Session", variable=self.record_var).pack(anchor="w", pady=2)
        
        if self.settings.get("advanced_open", False):
            self.toggle_advanced_options()
            
    def _build_create_tab(self):
        """Build the CREATE tab for content creators."""
        # Welcome message
        welcome_frame = ttk.Frame(self.create_tab)
        welcome_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            welcome_frame,
            text="🎨 Content Creation Hub",
            font=("Helvetica", 18, "bold"),
            fg="#2c3e50"
        ).pack()
        
        tk.Label(
            welcome_frame,
            text="Create characters, animations, and assets for MyCraft.\nNo coding required!",
            font=("Helvetica", 11),
            fg="#7f8c8d",
            justify=tk.CENTER
        ).pack(pady=(5, 0))
        
        # Workspace buttons
        workspaces_frame = ttk.LabelFrame(self.create_tab, text=" Choose a Workspace ", padding="20")
        workspaces_frame.pack(fill="both", expand=True)
        
        # Character Editor
        char_frame = ttk.Frame(workspaces_frame)
        char_frame.pack(fill="x", pady=10)
        
        char_btn = tk.Button(
            char_frame,
            text="🧍  Character Editor",
            font=("Helvetica", 14, "bold"),
            bg="#9b59b6",
            fg="white",
            activebackground="#a569bd",
            activeforeground="white",
            cursor="hand2",
            command=lambda: self.launch_editor("Character"),
            height=2
        )
        char_btn.pack(fill="x")
        
        tk.Label(
            char_frame,
            text="Customize skeleton proportions, bone positions, and body shapes",
            font=("Helvetica", 10),
            fg="#7f8c8d"
        ).pack(pady=(5, 0))
        
        # Animation Editor
        anim_frame = ttk.Frame(workspaces_frame)
        anim_frame.pack(fill="x", pady=10)
        
        anim_btn = tk.Button(
            anim_frame,
            text="🏃  Animation Editor",
            font=("Helvetica", 14, "bold"),
            bg="#e67e22",
            fg="white",
            activebackground="#f39c12",
            activeforeground="white",
            cursor="hand2",
            command=lambda: self.launch_editor("Animation"),
            height=2
        )
        anim_btn.pack(fill="x")
        
        tk.Label(
            anim_frame,
            text="Create walk cycles, attacks, and custom character animations",
            font=("Helvetica", 10),
            fg="#7f8c8d"
        ).pack(pady=(5, 0))
        
        # Preview Mode
        preview_frame = ttk.Frame(workspaces_frame)
        preview_frame.pack(fill="x", pady=10)
        
        preview_btn = tk.Button(
            preview_frame,
            text="👁️  Preview Mode",
            font=("Helvetica", 14, "bold"),
            bg="#1abc9c",
            fg="white",
            activebackground="#48c9b0",
            activeforeground="white",
            cursor="hand2",
            command=lambda: self.launch_editor("Preview"),
            height=2
        )
        preview_btn.pack(fill="x")
        
        tk.Label(
            preview_frame,
            text="Test your creations in a live 3D viewport",
            font=("Helvetica", 10),
            fg="#7f8c8d"
        ).pack(pady=(5, 0))
        
        # Help link
        help_frame = ttk.Frame(self.create_tab)
        help_frame.pack(fill="x", pady=(20, 0))
        
        ttk.Label(
            help_frame,
            text="💡 Tip: Press 1-3 in the editor to switch between workspaces",
            font=("Helvetica", 10),
            foreground="#95a5a6"
        ).pack()
        
    def _build_advanced_tab(self):
        """Build the ADVANCED tab for server hosting and dev options."""
        # Server Hosting
        host_frame = ttk.LabelFrame(self.advanced_tab, text=" Host a Game Server ", padding="15")
        host_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(host_frame, text="Run a server so others on your WiFi can join.", 
                  justify=tk.CENTER, foreground="#7f8c8d").pack(pady=(0, 15))
        
        self.server_btn = ttk.Button(host_frame, text="🚀 LAUNCH SERVER", command=self.launch_server, style="Host.TButton")
        self.server_btn.pack(fill="x", pady=5, ipady=10)
        
        # Join as Host button
        self.join_host_btn = ttk.Button(host_frame, text="🎮 Join as Host Player", command=self.join_as_host, style="Action.TButton")
        self.join_host_btn.pack(fill="x", pady=5, ipady=5)
        
        # Server status
        status_frame = ttk.Frame(host_frame)
        status_frame.pack(pady=10)
        ttk.Label(status_frame, text="Server Status: ").pack(side=tk.LEFT)
        self.server_status_label = tk.Label(status_frame, text="Checking...", font=("Helvetica", 10, "bold"))
        self.server_status_label.pack(side=tk.LEFT)
        
        # Dev Options
        dev_frame = ttk.LabelFrame(self.advanced_tab, text=" Developer Options ", padding="15")
        dev_frame.pack(fill="x", pady=(0, 15))
        
        self.dev_mode_var = tk.BooleanVar(value=self.settings.get("dev_mode", False))
        ttk.Checkbutton(dev_frame, text="Developer Mode (Enable debug logs)", variable=self.dev_mode_var).pack(anchor="w")
        
        ttk.Button(dev_frame, text="📂 Open Server Config", command=self.open_server_config, style="Small.TButton").pack(fill="x", pady=(15, 5))
        ttk.Button(dev_frame, text="📂 Open Playtest Config", command=self.open_playtest_config, style="Small.TButton").pack(fill="x", pady=5)
        
        # Tips
        tip_frame = ttk.Frame(self.advanced_tab)
        tip_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(
            tip_frame,
            text="💡 Tip: Launch server first, then click 'Join as Host Player' to play on your own server.",
            font=("Helvetica", 10),
            foreground="#95a5a6",
            wraplength=500
        ).pack()
        
    def _show_first_launch_wizard(self):
        """Show first-launch wizard to guide new users."""
        wizard = FirstLaunchWizard(self.root)
        choice = wizard.show()
        
        # Mark as launched
        self.settings["has_launched_before"] = True
        self.save_settings()
        
        # Switch to appropriate tab
        if choice == "create":
            self.notebook.select(1)  # CREATE tab
        # else stay on PLAY tab (default)

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _check_server_active(self):
        """Check if local server is in the discovery list instead of TCP pinging."""
        for s in self.discovered_servers:
            if s.ip == "127.0.0.1" or s.ip == self.local_ip:
                return True
        return False

    def _update_server_status(self):
        """Update the status indicator. Refreshes discovery if needed."""
        is_active = self._check_server_active()
        
        if is_active:
            self.server_status_label.config(text="● RUNNING", fg="#27ae60")
        else:
            self.server_status_label.config(text="○ NOT RUNNING", fg="#e74c3c")
            if not getattr(self, '_last_refresh', 0) or time.time() - self._last_refresh > 5:
                 self.refresh_servers()
        
        # Check if we should enable Join button
        host = self.host_entry.get().strip()
        if host or is_active:
            self.join_btn.config(state="normal")
        else:
            self.join_btn.config(state="disabled")
            
        self.root.after(2000, self._update_server_status)

    def refresh_servers(self):
        self._last_refresh = time.time()
        self.status_var.set("Scanning for servers...")
        self.refresh_btn.config(state="disabled")
        
        thread = threading.Thread(target=self._scan_thread)
        thread.daemon = True
        thread.start()

    def _scan_thread(self):
        servers = find_servers(timeout=1.5)
        self.root.after(0, self._update_list, servers)

    def _update_list(self, servers):
        self.server_list.delete(0, tk.END)
        self.refresh_btn.config(state="normal")
        self.status_var.set(f"Found {len(servers)} servers")
        
        self.discovered_servers = servers
        if not servers:
            self.server_list.insert(tk.END, "  No servers found on your network")
        else:
            for s in servers:
                self.server_list.insert(tk.END, f"  {s.name} | {s.ip}:{s.port} | {s.player_count}/{s.max_players} Players")
            
            current_host = self.host_entry.get().strip()
            if not current_host or current_host == "localhost" or current_host == "127.0.0.1":
                self.host_entry.delete(0, tk.END)
                self.host_entry.insert(0, servers[0].ip)

    def on_server_select(self, event):
        selection = self.server_list.curselection()
        if selection:
            index = selection[0]
            if index < len(self.discovered_servers):
                server = self.discovered_servers[index]
                self.host_entry.delete(0, tk.END)
                self.host_entry.insert(0, server.ip)
    
    def load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_settings(self):
        try:
            settings = {
                "player_name": self.name_entry.get().strip() if hasattr(self, 'name_entry') else self.settings.get("player_name", "Player"),
                "server_host": self.host_entry.get().strip() if hasattr(self, 'host_entry') else self.settings.get("server_host", "localhost"),
                "preset": self.preset_var.get() if hasattr(self, 'preset_var') else self.settings.get("preset", "creative"),
                "use_config": self.use_config_var.get() if hasattr(self, 'use_config_var') else self.settings.get("use_config", True),
                "record_session": self.record_var.get() if hasattr(self, 'record_var') else self.settings.get("record_session", False),
                "dev_mode": self.dev_mode_var.get() if hasattr(self, 'dev_mode_var') else self.settings.get("dev_mode", False),
                "sensitivity": self.sens_var.get() if hasattr(self, 'sens_var') else self.settings.get("sensitivity", 40.0),
                "fov": self.fov_var.get() if hasattr(self, 'fov_var') else self.settings.get("fov", 90),
                "advanced_open": self.advanced_visible,
                "has_launched_before": self.settings.get("has_launched_before", False)
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def _test_connection(self, host, port):
        """Test if a server is reachable before committing."""
        try:
            self.status_var.set(f"Verifying {host}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def launch_single_player(self):
        """Direct launch without networking flags."""
        player_name = self.name_entry.get().strip() or "Player"
        preset = self.preset_var.get()
        use_config = self.use_config_var.get()
        record = self.record_var.get()
        
        self.save_settings()
        
        cmd = [sys.executable, "run_client.py", 
               "--preset", preset, 
               "--name", player_name,
               "--sensitivity", str(self.sens_var.get()),
               "--fov", str(self.fov_var.get())]
        
        if use_config:
            cmd.extend(["--config", "config/playtest.json"])
        if record:
            cmd.extend(["--record", f"{player_name}_{int(time.time())}"])
            
        print(f"Launching Single Player: {' '.join(cmd)}")
        self.status_var.set("Launching game...")
        
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                return_code = proc.wait(timeout=2.0)
                if return_code != 0:
                    stderr = proc.stderr.read()
                    self._handle_launch_error("Single Player", stderr)
                else:
                    self.status_var.set("Game started successfully!")
                    self.root.after(2000, self.root.destroy)
            except subprocess.TimeoutExpired:
                self.status_var.set("Game launched! Close this window or leave it open.")
                self._enable_close_button()
        except Exception as e:
            self._handle_launch_error("Single Player", str(e))

    def launch_multiplayer(self):
        """Connection with validation and fallback."""
        player_name = self.name_entry.get().strip() or "Player"
        host = self.host_entry.get().strip()
        preset = self.preset_var.get()
        use_config = self.use_config_var.get()
        record = self.record_var.get()
        
        if not host:
            messagebox.showwarning("No Server", "Please enter a server address or select from the list.")
            return

        if not self._test_connection(host, 5420):
            msg = f"Could not reach {host}:5420.\n\n"
            if host == "localhost" or host == "127.0.0.1":
                msg += "Is your server running? (Go to ADVANCED tab and click LAUNCH SERVER)"
            else:
                msg += "Check if the host started their server and that you are on the same WiFi."
            
            response = messagebox.askyesno("Connection Failed", f"{msg}\n\nLaunch Single Player instead?")
            if response:
                self.launch_single_player()
            else:
                self.status_var.set("Connection failed.")
            return

        self.save_settings()
        
        cmd = [sys.executable, "run_client.py", 
               "--host", host, 
               "--preset", preset, 
               "--name", player_name,
               "--sensitivity", str(self.sens_var.get()),
               "--fov", str(self.fov_var.get())]
        
        if use_config:
            cmd.extend(["--config", "config/playtest.json"])
        if record:
            cmd.extend(["--record", f"{player_name}_{int(time.time())}"])
            
        print(f"Launching Multiplayer: {' '.join(cmd)}")
        self.status_var.set("Launching multiplayer...")
        
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                return_code = proc.wait(timeout=2.0)
                if return_code != 0:
                    stderr = proc.stderr.read()
                    self._handle_launch_error("Multiplayer", stderr)
                else:
                    self.status_var.set("Game started successfully!")
                    self.root.after(2000, self.root.destroy)
            except subprocess.TimeoutExpired:
                self.status_var.set("Game launched! Close this window or leave it open.")
                self._enable_close_button()
        except Exception as e:
            self._handle_launch_error("Multiplayer", str(e))
    
    def launch_server(self):
        self.save_settings()
        
        if sys.platform == "win32":
            subprocess.Popen(["start", "cmd", "/k", sys.executable, "run_server.py"], shell=True)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Terminal", sys.executable, "run_server.py"])
        else:
            terminals = ["gnome-terminal", "konsole", "xterm", "x-terminal-emulator"]
            for term in terminals:
                try:
                    if term == "gnome-terminal":
                        subprocess.Popen([term, "--", sys.executable, "run_server.py"])
                    else:
                        subprocess.Popen([term, "-e", f"{sys.executable} run_server.py{' --debug' if self.dev_mode_var.get() else ''}"])
                    break
                except FileNotFoundError:
                    continue
            else:
                messagebox.showwarning("No Terminal", "Could not find a terminal emulator.")
        
        self.status_var.set("Server launch command sent!")
        self.root.after(2000, lambda: self.status_var.set("Server active!" if self._check_server_active() else "Server starting..."))
    
    def join_as_host(self):
        """Join the local server as a player (for host to play on their own server)."""
        if not self._check_server_active():
            response = messagebox.askyesno(
                "Server Not Running",
                "The server doesn't appear to be running.\n\nWould you like to launch it first?"
            )
            if response:
                self.launch_server()
                self.root.after(3000, self.join_as_host)
            return
        
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, "127.0.0.1")
        self.launch_multiplayer()
    
    def launch_editor(self, workspace: str = None):
        """Launch the editor suite with an optional workspace selection."""
        self.save_settings()
        
        cmd = [sys.executable, "run_editor.py"]
        if workspace:
            cmd.extend(["--workspace", workspace])
            
        print(f"Launching Editor: {' '.join(cmd)}")
        self.status_var.set(f"Launching {workspace or 'Editor'}...")
        
        try:
            subprocess.Popen(cmd)
            self.status_var.set(f"{workspace or 'Editor'} launched!")
        except Exception as e:
            self._handle_launch_error("Editor", str(e))
    
    def _handle_launch_error(self, mode, error_msg):
        """Handle game launch errors gracefully."""
        self.status_var.set(f"{mode} launch failed - see error")
        
        error_lower = error_msg.lower()
        
        if "modulenotfounderror" in error_lower and "panda3d" in error_lower:
            user_msg = (
                "Missing dependency: Panda3D\n\n"
                "Please install dependencies:\n"
                "  pip install -r requirements.txt\n\n"
                "If using a venv, make sure it's activated!"
            )
        elif "modulenotfounderror" in error_lower:
            user_msg = (
                f"Missing Python module\n\n"
                f"Please install dependencies:\n"
                f"  pip install -r requirements.txt\n\n"
                f"Error: {error_msg[:200]}"
            )
        elif "permission denied" in error_lower:
            user_msg = (
                "Permission error\n\n"
                "Make sure run_client.py is executable\n"
                "and you have write permissions in this directory."
            )
        else:
            user_msg = (
                f"Failed to start\n\n"
                f"Error details: {error_msg[:300]}\n\n"
                f"Check logs/ folder for more information."
            )
        
        response = messagebox.askretrycancel(f"{mode} Launch Failed", user_msg)
        if response:
            if mode == "Single Player":
                self.launch_single_player()
            elif mode == "Multiplayer":
                self.launch_multiplayer()
            elif mode == "Editor":
                self.launch_editor()
        else:
            self.status_var.set("Launch cancelled - ready to try again")
    
    def update_preset_desc(self, event=None):
        """Update description based on selected preset."""
        preset = self.preset_var.get()
        descs = {
            'creative': "Fly (Space/Shift), God Mode, Debug Info",
            'testing': "Standard survival feel + Debug Info",
            'performance': "Standard feel, Debug OFF, Optimized"
        }
        self.preset_desc.config(text=descs.get(preset, ""))

    def toggle_advanced_options(self):
        """Toggle visibility of advanced settings in PLAY tab."""
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.adv_frame.pack(fill="x", pady=10)
            self.adv_btn.config(text="⚙️ More Options ▲")
        else:
            self.adv_frame.pack_forget()
            self.adv_btn.config(text="⚙️ More Options ▼")
    
    def open_server_config(self):
        """Open server_config.json in default editor."""
        config_path = Path("config/server_config.json")
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump({"broadcast_rate": 20, "max_players": 16, "debug": False, "port": 5420}, f, indent=4)
        
        self._open_file(config_path)
        
    def open_playtest_config(self):
        """Open playtest.json in default editor."""
        config_path = Path("config/playtest.json")
        if config_path.exists():
            self._open_file(config_path)
        else:
            messagebox.showinfo("Not Found", f"Config file not found: {config_path}")
            
    def _open_file(self, path):
        """Open a file with the system default application."""
        try:
            import os
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def _enable_close_button(self):
        """Add a close button after successful launch."""
        if hasattr(self, '_close_button_added'):
            return
        self._close_button_added = True
        
        close_btn = ttk.Button(
            self.root,
            text="Close Launcher",
            command=self.root.destroy
        )
        close_btn.pack(side=tk.BOTTOM, pady=10)


if __name__ == "__main__":
    try:
        if sys.platform == "linux":
            import os
            os.environ["TK_SILENCE_DEPRECATION"] = "1"
            
        root = tk.Tk()
        app = MyCraftLauncher(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Launcher crashed: {e}")
