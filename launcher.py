#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import threading
from network.discovery import find_servers

class MyCraftLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("MyCraft Launcher")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header_frame = tk.Frame(root, bg="#2c3e50", height=60)
        header_frame.pack(fill="x")
        title_label = tk.Label(header_frame, text="MyCraft Playtest", font=("Helvetica", 24, "bold"), bg="#2c3e50", fg="white")
        title_label.pack(pady=10)
        
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Server IP
        ttk.Label(main_frame, text="Server Address:").grid(row=0, column=0, sticky="w", pady=5)
        self.host_entry = ttk.Entry(main_frame, width=40)
        self.host_entry.insert(0, "localhost")
        self.host_entry.grid(row=0, column=1, columnspan=2, pady=5)
        
        # Presets
        ttk.Label(main_frame, text="Play Style:").grid(row=1, column=0, sticky="w", pady=5)
        self.preset_var = tk.StringVar(value="creative")
        preset_combo = ttk.Combobox(main_frame, textvariable=self.preset_var, state="readonly")
        preset_combo['values'] = ('creative', 'testing', 'performance')
        preset_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        
        # Config (Hot-Reload)
        self.use_config_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Enable Hot-Reload Config", variable=self.use_config_var).grid(row=2, column=1, sticky="w")
        
        # Server List
        ttk.Label(main_frame, text="Discovered LAN Servers:").grid(row=3, column=0, sticky="w", pady=(15, 5))
        self.refresh_btn = ttk.Button(main_frame, text="Refresh", command=self.refresh_servers)
        self.refresh_btn.grid(row=3, column=2, sticky="e", pady=(15, 5))
        
        self.server_list = tk.Listbox(main_frame, height=6)
        self.server_list.grid(row=4, column=0, columnspan=3, sticky="ew", pady=5)
        self.server_list.bind('<<ListboxSelect>>', self.on_server_select)
        
        # Connect Button
        self.launch_btn = ttk.Button(root, text="LAUNCH GAME", command=self.launch_game)
        self.launch_btn.pack(fill="x", padx=20, pady=20, ipady=10)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial Refresh
        self.refresh_servers()

    def refresh_servers(self):
        self.server_list.delete(0, tk.END)
        self.server_list.insert(tk.END, "Searching...")
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
            self.server_list.insert(tk.END, "No servers found")
        else:
            for s in servers:
                self.server_list.insert(tk.END, f"{s.name} | {s.ip}:{s.port} | {s.player_count}/{s.max_players} Players")

    def on_server_select(self, event):
        selection = self.server_list.curselection()
        if selection:
            index = selection[0]
            if index < len(self.discovered_servers):
                server = self.discovered_servers[index]
                self.host_entry.delete(0, tk.END)
                self.host_entry.insert(0, server.ip)

    def launch_game(self):
        host = self.host_entry.get().strip()
        preset = self.preset_var.get()
        use_config = self.use_config_var.get()
        
        cmd = [sys.executable, "run_client.py", "--host", host, "--preset", preset]
        
        if use_config:
            cmd.extend(["--config", "config/playtest.json"])
            
        print(f"Launching: {' '.join(cmd)}")
        self.root.destroy()
        subprocess.Popen(cmd)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MyCraftLauncher(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start launcher: {e}")
