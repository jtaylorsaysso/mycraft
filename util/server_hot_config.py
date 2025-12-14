"""
Async Server-Side Hot-Reload Configuration System

Watches a JSON config file for changes and updates server settings in real-time.
Designed for use with asyncio server loop.
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List, Awaitable
from dataclasses import dataclass
import logging

from util.logger import get_logger

class ServerHotConfig:
    """
    Async-compatible hot config watcher for GameServer.
    """
    
    # Default server configuration parameters
    DEFAULTS = {
        "broadcast_rate": 20,
        "max_players": 16,
        "debug": False,
        "port": 5420,  # Note: Port changes require restart
        "discovery_enabled": True
    }
    
    def __init__(self, config_path: Optional[Path] = None, check_interval: float = 1.0):
        """
        Initialize the server hot config watcher.
        
        Args:
            config_path: Path to JSON config file.
            check_interval: How often to check for file changes (seconds).
        """
        self._config_path = Path(config_path) if config_path else None
        self._check_interval = check_interval
        self._last_check_time: float = 0.0
        self._last_mtime: float = 0.0
        self._values: Dict[str, Any] = dict(self.DEFAULTS)
        
        # Callbacks receive (key, value)
        self._callbacks: List[Callable[[str, Any], None]] = []
        
        self.logger = get_logger("ServerHotConfig")
        
        # Load initial config
        if self._config_path:
            self.load_config()
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if default is not None:
            return self._values.get(key, default)
        return self._values.get(key, self.DEFAULTS.get(key))
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (in-memory only)."""
        old_value = self._values.get(key)
        self._values[key] = value
        
        if old_value != value:
            self.notify_change(key, value)
            
    def on_change(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for when any config value changes."""
        self._callbacks.append(callback)
        
    def load_config(self) -> None:
        """Load configuration from file synchronously."""
        if not self._config_path or not self._config_path.exists():
            return
            
        try:
            current_mtime = self._config_path.stat().st_mtime
            self._last_mtime = current_mtime
            
            with self._config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                
            updates = []
            for key, value in data.items():
                old_value = self._values.get(key)
                self._values[key] = value
                
                if old_value != value:
                    updates.append((key, value))
            
            if updates:
                self.logger.info(f"Loaded config from {self._config_path}")
                for key, val in updates:
                    self.notify_change(key, val)
                    
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(f"Failed to load config: {e}")

    async def update_loop(self):
        """
        Async task to periodically check for config file changes.
        Run this as a background task in the server.
        """
        while True:
            await asyncio.sleep(self._check_interval)
            try:
                if self._check_needed():
                    # We run blocking I/O in executor to avoid blocking event loop
                    # though stat() is fast, it's good practice
                    await asyncio.get_running_loop().run_in_executor(None, self.load_config)
            except Exception as e:
                self.logger.error(f"Error in config update loop: {e}")

    def _check_needed(self) -> bool:
        """Check if file might have changed based on simple interval."""
        if not self._config_path or not self._config_path.exists():
            return False
            
        current_time = time.time()
        # Only check filesystem periodically
        if current_time - self._last_check_time < self._check_interval:
            return False
            
        self._last_check_time = current_time
        
        # Check mtime
        try:
            mtime = self._config_path.stat().st_mtime
            return mtime != self._last_mtime
        except OSError:
            return False

    def notify_change(self, key: str, value: Any) -> None:
        """Notify all callbacks of a value change."""
        self.logger.info(f"Config change: {key} = {value}")
        for callback in self._callbacks:
            try:
                callback(key, value)
            except Exception as e:
                self.logger.error(f"Callback error for {key}: {e}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return dict(self._values)

    def save(self) -> None:
        """Save current values back to file."""
        if not self._config_path:
            return
            
        try:
            with self._config_path.open("w", encoding="utf-8") as f:
                json.dump(self._values, f, indent=2)
            self.logger.info(f"Saved config to {self._config_path}")
            # Update mtime so we don't trigger a reload loop
            self._last_mtime = self._config_path.stat().st_mtime
        except OSError as e:
            self.logger.error(f"Failed to save config: {e}")
