from typing import List, Dict, TYPE_CHECKING
import contextlib

if TYPE_CHECKING:
    from network.server import GameServer

class CommandProcessor:
    """Handles parsing and execution of admin commands."""
    
    def __init__(self, server: 'GameServer', player_manager):
        self.server = server
        self.player_manager = player_manager
        
        # Access config from server
        self.config = getattr(server, 'config', None)

    async def process_command(self, player_id: str, command: str) -> List[str]:
        """Execute an admin command string issued by a client player."""
        command = (command or "").strip()
        if not command:
            return []

        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]
        lines: List[str] = []

        if cmd in {"/help", "/?"}:
            lines.append("Available commands:")
            lines.append("  /help                 Show this help")
            lines.append("  /list                 List players (including host)")
            lines.append("  /kick <player_id>     Disconnect a player")
            lines.append("  /hostpos x y z        Move host player to position")
            lines.append("  /hostrot yaw          Set host Y rotation in degrees")
            lines.append("  /set <param> <val>    Set server config parameter")
            lines.append("  /get <param>          Get server config parameter")
            lines.append("  /config               List all config values")
            lines.append("  /reload               Reload config from file")
            lines.append("  /quit                 Shut down the server")

        elif cmd == "/list":
            players = self.player_manager.get_all_players()
            if not players:
                lines.append("No players.")
            else:
                for pid, state in players.items():
                    tag = " (host)" if pid == self.player_manager.host_player_id or state.get("is_host") else ""
                    pos = state.get("pos")
                    rot = state.get("rot_y")
                    lines.append(f"- {pid}{tag} pos={pos} rot_y={rot}")

        elif cmd == "/kick":
            if not args:
                lines.append("Usage: /kick <player_id>")
            else:
                pid = args[0]
                if pid == self.player_manager.host_player_id:
                    lines.append("Cannot kick the host player.")
                else:
                    # We need to call back to server to actually disconnect the socket
                    # This coupling is somewhat expected for network controls
                    ok = await self.kick_player(pid)
                    if ok:
                        lines.append(f"Kicked {pid}.")
                    else:
                        lines.append(f"No such player: {pid}")

        elif cmd == "/hostpos":
            if len(args) != 3:
                lines.append("Usage: /hostpos x y z")
            else:
                try:
                    x, y, z = map(float, args)
                    self.player_manager.set_host_position(x, y, z)
                    lines.append(f"Host moved to ({x}, {y}, {z}).")
                except ValueError:
                    lines.append("Coordinates must be numbers.")

        elif cmd == "/hostrot":
            if len(args) != 1:
                lines.append("Usage: /hostrot yaw")
            else:
                try:
                    yaw = float(args[0])
                    self.player_manager.set_host_rotation(yaw)
                    lines.append(f"Host rotation set to {yaw}.")
                except ValueError:
                    lines.append("Yaw must be a number.")

                except ValueError:
                    lines.append("Yaw must be a number.")

        elif cmd == "/set":
            if not self.config:
                lines.append("Configuration system not authenticated.")
            elif len(args) != 2:
                lines.append("Usage: /set <parameter> <value>")
            else:
                key = args[0]
                val_str = args[1]
                
                # Check if parameter exists in defaults
                if key not in self.config.DEFAULTS:
                     lines.append(f"Unknown parameter: {key}")
                elif key == "port":
                     lines.append("Cannot change port while server is running.")
                else:
                    # Parse value based on default type
                    default_val = self.config.DEFAULTS[key]
                    try:
                        if isinstance(default_val, bool):
                            if val_str.lower() == 'true': val = True
                            elif val_str.lower() == 'false': val = False
                            else: raise ValueError("Must be true or false")
                        elif isinstance(default_val, int):
                            val = int(val_str)
                            # Clamping logic
                            if key == "broadcast_rate": val = max(5, min(120, val))
                            elif key == "max_players": val = max(1, min(64, val))
                        elif isinstance(default_val, float):
                            val = float(val_str)
                        else:
                            val = val_str
                            
                        self.config.set(key, val)
                        lines.append(f"Set {key} to {val}")
                        
                        # Broadcast change to all admins (host)
                        # In the future we might want to announce "Server config changed" to all
                        
                    except ValueError:
                         lines.append(f"Invalid value for {key} (expected {type(default_val).__name__})")

        elif cmd == "/get":
            if not self.config:
                lines.append("Configuration system not available.")
            elif len(args) != 1:
                lines.append("Usage: /get <parameter>")
            else:
                key = args[0]
                val = self.config.get(key)
                if val is None and key not in self.config.DEFAULTS:
                    lines.append(f"Unknown parameter: {key}")
                else:
                    lines.append(f"{key}: {val}")

        elif cmd == "/config":
            if not self.config:
                lines.append("Configuration system not available.")
            else:
                lines.append("=== Server Configuration ===")
                all_vals = self.config.get_all()
                for k, v in all_vals.items():
                    tag = " (read-only)" if k == "port" else ""
                    lines.append(f"{k}: {v}{tag}")

        elif cmd == "/reload":
            if not self.config:
                lines.append("Configuration system not available.")
            else:
                try:
                    # Run synchronous load in executor to avoid blocking
                    import asyncio
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, self.config.load_config)
                    lines.append("Server config reloaded from file.")
                except Exception as e:
                    lines.append(f"Failed to reload config: {e}")

            lines.append("Shutting down server...")
            self.server.running = False
            if self.server.server is not None:
                self.server.server.close()

        else:
            lines.append(f"Unknown command: {cmd}. Try /help")

        return lines

    async def kick_player(self, player_id: str) -> bool:
        """Disconnect a player by ID. Returns True if a player was kicked."""
        if player_id == self.player_manager.host_player_id:
            return False

        # Access clients directly from server instance
        writer = self.server.clients.get(player_id)
        if writer is None:
            return False

        try:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
        except Exception:
            pass

        # Server's handle_disconnect will be triggered by the closed socket locally 
        # or we might need to call it manually if we want immediate cleanup
        # typically wait_closed() handles the IO aspect, but `handle_disconnect` 
        # is usually called by the reader loop when it detects EOF.
        # To be safe and immediate, we can call logic.
        
        # However, calling handle_disconnect might race with the reader loop 
        # finding the closed connection. 
        # The original code called handle_disconnect explicitly.
        
        await self.server.handle_disconnect(player_id)
        return True
