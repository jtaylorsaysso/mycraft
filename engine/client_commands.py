"""
Client-side Command Processor for MyCraft Playtesting

Handles local-only commands for the player during playtesting.
"""

from typing import List, Optional, Callable, Dict, Any, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from engine.player import Player
    from engine.input_handler import InputHandler
    from util.hot_config import HotConfig


class ClientCommandProcessor:
    """Handles client-side slash commands for playtesting."""
    
    def __init__(
        self,
        player: 'Player',
        input_handler: 'InputHandler',
        spawn_pos: tuple = (10, 2, 10),
        config: Optional['HotConfig'] = None
    ):
        self.player = player
        self.input_handler = input_handler
        self.spawn_pos = spawn_pos
        self.config = config
        self._recorder = None
        self._player_session = None  # SessionPlayer for replay
        self._info_callback: Optional[Callable[[], Dict[str, Any]]] = None
    
    def set_recorder(self, recorder) -> None:
        """Set the session recorder for /record command."""
        self._recorder = recorder
    
    def set_session_player(self, player) -> None:
        """Set the session player for /replay command."""
        self._player_session = player
    
    def set_info_callback(self, callback: Callable[[], Dict[str, Any]]) -> None:
        """Set callback for getting session info (FPS, chunks, etc.)."""
        self._info_callback = callback
    
    def process_command(self, command: str) -> List[str]:
        """
        Execute a command string. Returns list of output lines.
        """
        command = (command or "").strip()
        if not command:
            return []
        
        # Handle commands that don't start with /
        if not command.startswith("/"):
            return [f"Unknown input. Try /help"]
        
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]
        lines: List[str] = []
        
        if cmd in {"/help", "/?"}:
            lines.append("Playtest Commands:")
            lines.append("  /tp <x> <y> <z>    Teleport to position")
            lines.append("  /speed <mult>      Set speed multiplier (0.5-5.0)")
            lines.append("  /god               Toggle god mode (flight)")
            lines.append("  /info              Show session info")
            lines.append("  /spawn             Return to spawn point")
            lines.append("  /sensitivity <val> Set mouse sensitivity")
            lines.append("  /record <name>     Start recording session")
            lines.append("  /stoprec           Stop recording and save")
            lines.append("  /record <name>     Start recording session")
            lines.append("  /stoprec           Stop recording and save")
            lines.append("  /replay <file>     Play back a recording")
            lines.append("  /set <param> <val> Set config parameter")
            lines.append("  /get <param>       Get config parameter")
            lines.append("  /config            List all config values")
            lines.append("  /reload            Reload from file")
            lines.append("  /save              Save changes to file")
            lines.append("  /debug collision   Toggle collision debug viz (also F3)")
        
        elif cmd == "/tp":
            if len(args) != 3:
                lines.append("Usage: /tp <x> <y> <z>")
            else:
                try:
                    x, y, z = map(float, args)
                    self.player.position = (x, y, z)
                    lines.append(f"Teleported to ({x:.1f}, {y:.1f}, {z:.1f})")
                except ValueError:
                    lines.append("Coordinates must be numbers.")
        
        elif cmd == "/speed":
            if len(args) != 1:
                lines.append("Usage: /speed <multiplier>")
            else:
                try:
                    mult = float(args[0])
                    mult = max(0.5, min(5.0, mult))  # Clamp
                    base_speed = 6.0
                    self.input_handler.movement_speed = base_speed * mult
                    self.input_handler.fly_speed = 12.0 * mult
                    lines.append(f"Speed multiplier set to {mult:.1f}x")
                except ValueError:
                    lines.append("Multiplier must be a number.")
        
        elif cmd == "/god":
            self.input_handler.god_mode = not self.input_handler.god_mode
            status = "ON" if self.input_handler.god_mode else "OFF"
            lines.append(f"God mode: {status}")
        
        elif cmd == "/spawn":
            x, y, z = self.spawn_pos
            self.player.position = (x, y, z)
            lines.append(f"Returned to spawn ({x:.1f}, {y:.1f}, {z:.1f})")
        
        elif cmd == "/sensitivity":
            if len(args) != 1:
                lines.append("Usage: /sensitivity <value>")
            else:
                try:
                    val = float(args[0])
                    val = max(5.0, min(200.0, val))  # Clamp
                    self.input_handler.mouse_sensitivity = val
                    lines.append(f"Mouse sensitivity set to {val:.1f}")
                except ValueError:
                    lines.append("Sensitivity must be a number.")
        
        elif cmd == "/info":
            info = self._get_info()
            lines.append(f"Position: ({info['x']:.1f}, {info['y']:.1f}, {info['z']:.1f})")
            lines.append(f"Rotation: {info['rot_y']:.1f}°")
            lines.append(f"God Mode: {info['god_mode']}")
            lines.append(f"Speed: {info['speed']:.1f}")
            if self._info_callback:
                extra = self._info_callback()
                for key, val in extra.items():
                    lines.append(f"{key}: {val}")
        
        elif cmd == "/record":
            if self._recorder is None:
                lines.append("Recording not available.")
            elif self._recorder.is_recording():
                lines.append("Already recording. Use /stoprec to stop.")
            elif len(args) != 1:
                lines.append("Usage: /record <session_name>")
            else:
                name = args[0]
                pos = (self.player.position.x, self.player.position.y, self.player.position.z)
                self._recorder.start(spawn_pos=pos)
                self._recorder._pending_save_name = name  # Store for save
                lines.append(f"Recording started: {name}")
        
        elif cmd == "/stoprec":
            if self._recorder is None or not self._recorder.is_recording():
                lines.append("Not currently recording.")
            else:
                self._recorder.stop()
                name = getattr(self._recorder, '_pending_save_name', 'session')
                path = Path("recordings") / f"{name}.json"
                self._recorder.save(path)
                stats = self._recorder.get_stats()
                lines.append(f"Recording saved: {path}")
                lines.append(f"Duration: {stats['duration']:.1f}s, Events: {stats['event_count']}")
        
        elif cmd == "/replay":
            if self._player_session is None:
                lines.append("Replay not available.")
            elif len(args) != 1:
                lines.append("Usage: /replay <file>")
            else:
                filename = args[0]
                # Try with and without .json extension
                path = Path("recordings") / filename
                if not path.suffix:
                    path = path.with_suffix(".json")
                
                if self._player_session.load(path):
                    spawn = self._player_session.get_spawn_pos()
                    if spawn:
                        self.player.position = spawn
                    self._player_session.start()
                    lines.append(f"Replaying: {path.name}")
                else:
                    lines.append(f"Failed to load: {path}")
        
        elif cmd == "/set":
            if not self.config:
                lines.append("Config system not available.")
            elif len(args) != 2:
                lines.append("Usage: /set <param> <value>")
            else:
                key = args[0]
                val_str = args[1]
                
                # Handle aliases
                if key == "speed": key = "movement_speed"
                elif key == "sens": key = "mouse_sensitivity"
                elif key == "chunks": key = "chunk_load_radius"
                
                if key not in self.config.DEFAULTS and key not in self.config._values:
                    lines.append(f"Unknown parameter: {key}")
                else:
                    # Generic type inference from default value
                    default_val = self.config.DEFAULTS.get(key, 0.0)
                    try:
                        if isinstance(default_val, bool):
                             val = val_str.lower() == "true"
                        elif isinstance(default_val, int):
                             val = int(val_str)
                             # Clamps
                             if key == "chunk_load_radius": val = max(1, min(10, val))
                        elif isinstance(default_val, float):
                             val = float(val_str)
                             # Clamps
                             if key == "movement_speed": val = max(1.0, min(30.0, val))
                             elif key == "jump_height": val = max(0.5, min(15.0, val))
                        else:
                             val = val_str
                             
                        self.config.set(key, val)
                        lines.append(f"Set {key} to {val}")
                        
                        # Also update local input handler immediately if needed
                        # (InputHandler subscribes, but some might be direct)
                        if key == "movement_speed": self.input_handler.movement_speed = val
                        elif key == "mouse_sensitivity": self.input_handler.mouse_sensitivity = val
                        
                    except ValueError:
                        lines.append(f"Invalid value type for {key}")

        elif cmd == "/get":
            if not self.config:
                lines.append("Config system not available.")
            elif len(args) != 1:
                lines.append("Usage: /get <param>")
            else:
                key = args[0]
                val = self.config.get(key)
                if val is not None:
                     lines.append(f"{key}: {val}")
                else:
                     lines.append(f"Unknown parameter: {key}")

        elif cmd == "/config":
            if not self.config:
                 lines.append("Config system not available.")
            else:
                lines.append("=== Client Configuration ===")
                # Group by simple categories (heuristic)
                cats = {
                    "Physics": ["speed", "jump", "gravity", "god"],
                    "Camera": ["fov", "cam", "view"],
                    "Anim": ["walk", "idle"],
                    "World": ["chunk"]
                }
                
                sorted_keys = sorted(self.config.get_all().keys())
                for k in sorted_keys:
                    val = self.config.get(k)
                    lines.append(f"{k}: {val}")
                    
        elif cmd == "/reload":
            if self.config:
                self.config.load_config()
                lines.append("Config reloaded from file.")
            else:
                lines.append("Config system not available.")

        elif cmd == "/save":
            if self.config:
                self.config.save()
                lines.append("Config saved to file.")
            else:
                lines.append("Config system not available.")
        
        elif cmd == "/debug":
            if len(args) != 1:
                lines.append("Usage: /debug <feature> (e.g., collision)")
            elif args[0].lower() == "collision":
                enabled = self.input_handler.debug_renderer.toggle()
                lines.append(f"Collision debug: {'ON' if enabled else 'OFF'}")
            else:
                lines.append(f"Unknown debug feature: {args[0]}")

        else:
            lines.append(f"Unknown command: {cmd}. Try /help")
        
        return lines
    
    def _get_info(self) -> Dict[str, Any]:
        """Get current player info."""
        return {
            "x": self.player.position.x,
            "y": self.player.position.y,
            "z": self.player.position.z,
            "rot_y": self.player.rotation_y,
            "god_mode": "ON" if self.input_handler.god_mode else "OFF",
            "speed": self.input_handler.movement_speed,
        }
