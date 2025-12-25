#!/usr/bin/env python3
"""
MyCraft Launcher
Easy entry point for players - handles dependency checking and game launch
"""

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

class MyCraftLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("MyCraft Launcher")
        self.root.geometry("750x700")  # Slightly larger for new controls
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
        
        # Header
        header_frame = tk.Frame(root, bg="#2c3e50", height=90)
        header_frame.pack(fill="x")
        
        title_frame = tk.Frame(header_frame, bg="#2c3e50")
        title_frame.pack(pady=(15, 5))
        
        tk.Label(title_frame, text="MyCraft Playtest", font=("Helvetica", 28, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        tk.Label(title_frame, text=" v0.5", font=("Helvetica", 14), bg="#2c3e50", fg="#95a5a6").pack(side=tk.LEFT, pady=(10, 0))
        
        # Show Local IP
        self.local_ip = self._get_local_ip()
        ip_label = tk.Label(header_frame, text=f"Your LAN IP: {self.local_ip}", font=("Helvetica", 12), bg="#2c3e50", fg="#bdc3c7")
        ip_label.pack(pady=(0, 15))
        
        # Main Container
        main_container = ttk.Frame(root, padding="20")
        main_container.pack(fill="both", expand=True)
        
        # Two-Column Layout
        left_col = ttk.LabelFrame(main_container, text=" Host a Game ", padding="15")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        right_col = ttk.LabelFrame(main_container, text=" Join a Game ", padding="15")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # --- Left Column: Hosting ---
        ttk.Label(left_col, text="Run the server on this machine\nso others on your WiFi can join.", 
                  justify=tk.CENTER, foreground="#7f8c8d").pack(pady=(0, 20))
        
        self.server_btn = ttk.Button(left_col, text="🚀 LAUNCH SERVER", command=self.launch_server, style="Host.TButton")
        self.server_btn.pack(fill="x", pady=10, ipady=15)
        
        status_frame = ttk.Frame(left_col)
        status_frame.pack(pady=10)
        ttk.Label(status_frame, text="Server Status: ").pack(side=tk.LEFT)
        self.server_status_label = tk.Label(status_frame, text="Checking...", font=("Helvetica", 10, "bold"))
        self.server_status_label.pack(side=tk.LEFT)
        
        # Host Options
        host_opts = ttk.LabelFrame(left_col, text=" Host Options ", padding="10")
        host_opts.pack(fill="x", pady=20)
        
        self.dev_mode_var = tk.BooleanVar(value=self.settings.get("dev_mode", False))
        ttk.Checkbutton(host_opts, text="Developer Mode\n(Enable debug logs)", variable=self.dev_mode_var).pack(anchor="w")
        
        ttk.Button(host_opts, text="📂 Open Server Config", command=self.open_server_config, style="Small.TButton").pack(fill="x", pady=(10, 0))
        
        ttk.Label(left_col, text="Tip: Keep the server window open\nwhile others are playing.", 
                  justify=tk.CENTER, font=("Helvetica", 9, "italic"), foreground="#95a5a6").pack(side=tk.BOTTOM, pady=10)
        
        # --- Right Column: Joining ---
        # Player Name
        ttk.Label(right_col, text="Player Name:").pack(anchor="w", pady=(0, 2))
        self.name_entry = ttk.Entry(right_col, width=30)
        self.name_entry.insert(0, self.settings.get("player_name", "Player"))
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Presets
        ttk.Label(right_col, text="Play Style:").pack(anchor="w", pady=(0, 2))
        self.preset_var = tk.StringVar(value=self.settings.get("preset", "creative"))
        preset_combo = ttk.Combobox(right_col, textvariable=self.preset_var, state="readonly")
        preset_combo['values'] = ('creative', 'testing', 'performance')
        preset_combo.pack(fill="x", pady=(0, 5))
        preset_combo.bind('<<ComboboxSelected>>', self.update_preset_desc)
        
        self.preset_desc = tk.Label(right_col, text="", font=("Helvetica", 9), fg="#7f8c8d", anchor="w", justify=tk.LEFT)
        self.preset_desc.pack(fill="x", pady=(0, 15))
        self.update_preset_desc()
        
        # Server IP
        ttk.Label(right_col, text="Server Address:").pack(anchor="w", pady=(0, 2))
        self.host_entry = ttk.Entry(right_col, width=30)
        self.host_entry.insert(0, self.settings.get("server_host", "localhost"))
        self.host_entry.pack(fill="x", pady=(0, 5))
        
        # Action Buttons
        self.single_btn = ttk.Button(right_col, text="🎮 PLAY SINGLE PLAYER", command=self.launch_single_player, style="Action.TButton")
        self.single_btn.pack(fill="x", pady=5, ipady=5)
        
        self.join_btn = ttk.Button(right_col, text="🌐 JOIN LAN SERVER", command=self.launch_multiplayer, style="Action.TButton")
        self.join_btn.pack(fill="x", pady=5, ipady=5)
        
        # Advanced Settings Toggler
        self.adv_btn = ttk.Button(right_col, text="⚙️ Advanced Settings ▼", command=self.toggle_advanced, style="Small.TButton")
        self.adv_btn.pack(fill="x", pady=(15, 0))
        
        # Advanced Settings Frame (Hidden by default)
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
        
        # Checkboxes moved here
        self.use_config_var = tk.BooleanVar(value=self.settings.get("use_config", True))
        ttk.Checkbutton(self.adv_frame, text="Hot-Reload Config", variable=self.use_config_var).pack(anchor="w", pady=(10, 2))

        self.record_var = tk.BooleanVar(value=self.settings.get("record_session", False))
        ttk.Checkbutton(self.adv_frame, text="Record Session", variable=self.record_var).pack(anchor="w", pady=2)
        
        if self.settings.get("advanced_open", False):
            self.toggle_advanced()
        
        # --- Bottom: Server Discovery ---
        discovery_frame = ttk.Frame(main_container)
        discovery_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        
        ttk.Label(discovery_frame, text="Discovered LAN Servers:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.refresh_btn = ttk.Button(discovery_frame, text="🔄 Refresh", command=self.refresh_servers, width=10)
        self.refresh_btn.pack(side=tk.RIGHT)
        
        self.server_list = tk.Listbox(main_container, height=4, font=("Courier", 10))
        self.server_list.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 10))
        self.server_list.bind('<<ListboxSelect>>', self.on_server_select)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Helvetica", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Background Monitoring
        self._update_server_status()
        self.refresh_servers()

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
            # Check for both localhost and the actual local LAN IP
            if s.ip == "127.0.0.1" or s.ip == self.local_ip:
                return True
        return False

    def _update_server_status(self):
        """Update the status indicator. Refreshes discovery if needed."""
        # Rapid check of existing discovery data
        is_active = self._check_server_active()
        
        if is_active:
            self.server_status_label.config(text="● RUNNING", fg="#27ae60")
        else:
            self.server_status_label.config(text="○ NOT RUNNING", fg="#e74c3c")
            # If we don't see it, trigger a quick background refresh to be sure
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
        # self.server_list.delete(0, tk.END) # Don't clear list on auto-refresh to avoid flicker
        # self.server_list.insert(tk.END, "  Scanning for LAN servers...")
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
            
            # Auto-select first one if host entry is default/empty
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
                "player_name": self.name_entry.get().strip(),
                "server_host": self.host_entry.get().strip(),
                "preset": self.preset_var.get(),
                "use_config": self.use_config_var.get(),
                "record_session": self.record_var.get(),
                "dev_mode": self.dev_mode_var.get(),
                "sensitivity": self.sens_var.get(),
                "fov": self.fov_var.get(),
                "advanced_open": self.advanced_visible
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
            # Don't close launcher - keep it open for error reporting
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to fail or succeed
            try:
                return_code = proc.wait(timeout=2.0)
                if return_code != 0:
                    # Game crashed immediately
                    stderr = proc.stderr.read()
                    self._handle_launch_error("Single Player", stderr)
                else:
                    # Clean exit within 2 seconds (shouldn't happen for game)
                    self.status_var.set("Game started successfully!")
                    self.root.after(2000, self.root.destroy)
            except subprocess.TimeoutExpired:
                # Still running after 2 seconds - good!
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

        # Connectivity Pre-Check
        if not self._test_connection(host, 5420):
            msg = f"Could not reach {host}:5420.\n\n"
            if host == "localhost" or host == "127.0.0.1":
                msg += "Is your server running? (Click LAUNCH SERVER on the left)"
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
            # Don't close launcher - keep it open for error reporting
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to fail or succeed
            try:
                return_code = proc.wait(timeout=2.0)
                if return_code != 0:
                    # Game crashed immediately
                    stderr = proc.stderr.read()
                    self._handle_launch_error("Multiplayer", stderr)
                else:
                    # Clean exit within 2 seconds (shouldn't happen for game)
                    self.status_var.set("Game started successfully!")
                    self.root.after(2000, self.root.destroy)
            except subprocess.TimeoutExpired:
                # Still running after 2 seconds - good!
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
        # Brief delay then verify
        self.root.after(2000, lambda: self.status_var.set("Server active!" if self._check_server_active() else "Server starting..."))
    
    def _handle_launch_error(self, mode, error_msg):
        """Handle game launch errors gracefully."""
        self.status_var.set(f"{mode} launch failed - see error")
        
        # Parse error for common issues
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
            # Generic error
            user_msg = (
                f"Game failed to start\n\n"
                f"Error details: {error_msg[:300]}\n\n"
                f"Check logs/ folder for more information."
            )
        
        # Show error with option to retry or close
        response = messagebox.askretrycancel(f"{mode} Launch Failed", user_msg)
        if response:
            # User wants to retry
            if mode == "Single Player":
                self.launch_single_player()
            else:
                self.launch_multiplayer()
        else:
            # User cancelled - keep launcher open
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

    def toggle_advanced(self):
        """Toggle visibility of advanced settings."""
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.adv_frame.pack(fill="x", pady=10)
            self.adv_btn.config(text="⚙️ Advanced Settings ▲")
        else:
            self.adv_frame.pack_forget()
            self.adv_btn.config(text="⚙️ Advanced Settings ▼")
    
    def open_server_config(self):
        """Open server_config.json in default editor."""
        config_path = Path("config/server_config.json")
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            # Create default if missing
            with open(config_path, 'w') as f:
                json.dump({"broadcast_rate": 20, "max_players": 16, "debug": False, "port": 5420}, f, indent=4)
        
        try:
            if sys.platform == "win32":
                os.startfile(config_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", config_path])
            else:
                subprocess.call(["xdg-open", config_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open config file: {e}")

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
        # Needed for xdg-open on some linux distros
        if sys.platform == "linux":
            import os
            os.environ["TK_SILENCE_DEPRECATION"] = "1"
            
        root = tk.Tk()
        app = MyCraftLauncher(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Launcher crashed: {e}")
