from typing import List, Dict, TYPE_CHECKING
import contextlib

if TYPE_CHECKING:
    from network.server import GameServer

class CommandProcessor:
    """Handles parsing and execution of admin commands."""
    
    def __init__(self, server: 'GameServer', player_manager):
        self.server = server
        self.player_manager = player_manager

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

        elif cmd in {"/quit", "/exit", "/shutdown"}:
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
