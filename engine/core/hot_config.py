"""
Hot-Reload Configuration System for MyCraft Playtesting

Watches a JSON config file for changes and updates game settings in real-time.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field


@dataclass
class ConfigValue:
    """Tracks a configuration value with validation."""
    key: str
    default: Any
    validator: Optional[Callable[[Any], bool]] = None
    on_change: Optional[Callable[[Any], None]] = None


class HotConfig:
    """Watches a JSON config file and provides live-updating values."""
    
    # Default configuration values
    DEFAULTS = {
        # Player Physics
        "mouse_sensitivity": 40.0,
        "movement_speed": 6.0,
        "fly_speed": 12.0,
        "jump_height": 3.5,
        "gravity": -12.0,
        "god_mode": False,
        
        # Camera
        "debug_overlay": False,
        "view_distance": 5,
        "fov": 90,
        "camera_distance": 4.0,
        "camera_height": 2.0,
        "camera_side_offset": 1.0,
        
        # Animations
        "walk_frequency": 10.0,
        "walk_amplitude_arms": 35.0,
        "walk_amplitude_legs": 30.0,
        "idle_bob_speed": 2.0,
        "idle_bob_amount": 0.01,
        
        # World Generation/Loading
        "chunk_load_radius": 3,
        "chunk_unload_radius": 5,
        "max_chunks_per_frame": 1,
    }
    
    def __init__(self, config_path: Optional[Path] = None, check_interval: float = 1.0):
        """
        Initialize the hot config watcher.
        
        Args:
            config_path: Path to JSON config file. If None, uses defaults only.
            check_interval: How often to check for file changes (seconds).
        """
        self._config_path = Path(config_path) if config_path else None
        self._check_interval = check_interval
        self._last_check_time: float = 0.0
        self._last_mtime: float = 0.0
        self._values: Dict[str, Any] = dict(self.DEFAULTS)
        self._callbacks: List[Callable[[str, Any], None]] = []
        
        # Load initial config if file exists
        if self._config_path:
            self._load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if default is not None:
            return self._values.get(key, default)
        return self._values.get(key, self.DEFAULTS.get(key))
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (in memory only, not saved to file)."""
        old_value = self._values.get(key)
        self._values[key] = value
        
        if old_value != value:
            self._notify_change(key, value)
    
    def save(self) -> None:
        """Save current configuration to file."""
        if not self._config_path:
            return
            
        try:
            with open(self._config_path, 'w', encoding="utf-8") as f:
                json.dump(self._values, f, indent=4)
        except OSError as e:
            print(f"[HotConfig] Failed to save config: {e}")
    
    def on_change(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for when any config value changes."""
        self._callbacks.append(callback)
    
    def update(self) -> bool:
        """
        Check for config file changes and reload if needed.
        Call this periodically (e.g., each frame or in a timer).
        
        Returns True if config was reloaded.
        """
        if not self._config_path:
            return False
        
        current_time = time.time()
        if current_time - self._last_check_time < self._check_interval:
            return False
        
        self._last_check_time = current_time
        
        if not self._config_path.exists():
            return False
        
        try:
            current_mtime = self._config_path.stat().st_mtime
            if current_mtime != self._last_mtime:
                self._load_config()
                return True
        except OSError:
            pass
        
        return False
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self._config_path or not self._config_path.exists():
            return
        
        try:
            self._last_mtime = self._config_path.stat().st_mtime
            
            with self._config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Update values and notify of changes
            for key, value in data.items():
                old_value = self._values.get(key)
                self._values[key] = value
                
                if old_value != value:
                    self._notify_change(key, value)
                    
        except (json.JSONDecodeError, OSError) as e:
            print(f"[HotConfig] Failed to load config: {e}")
    
    def _notify_change(self, key: str, value: Any) -> None:
        """Notify all callbacks of a value change."""
        for callback in self._callbacks:
            try:
                callback(key, value)
            except Exception as e:
                print(f"[HotConfig] Callback error for {key}: {e}")
    
    def save_defaults(self, path: Optional[Path] = None) -> None:
        """Save default configuration to a file (useful for initial setup)."""
        target = Path(path) if path else self._config_path
        if not target:
            return
        
        target.parent.mkdir(parents=True, exist_ok=True)
        
        with target.open("w", encoding="utf-8") as f:
            json.dump(self.DEFAULTS, f, indent=2)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return dict(self._values)


# Global singleton instance
_config_instance: Optional[HotConfig] = None


def init_config(config_path: Optional[Path] = None) -> HotConfig:
    """Initialize the global config instance."""
    global _config_instance
    _config_instance = HotConfig(config_path)
    return _config_instance


def get_config() -> Optional[HotConfig]:
    """Get the global config instance."""
    return _config_instance
