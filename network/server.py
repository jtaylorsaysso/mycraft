import asyncio
import json
import socket
from typing import Dict, Set, List
import time
import logging

from util.logger import get_logger, time_block, log_metric


class GameServer:
    """Simple TCP server for LAN multiplayer on port 5420."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5420):
        self.host = host
        self.port = port
        self.server = None
        self.clients: Dict[str, asyncio.StreamWriter] = {}
        self.player_states: Dict[str, Dict] = {}
        self.next_player_id = 1
        self.tick_rate = 20  # Broadcast state 20 times per second
        self.tick_interval = 1.0 / self.tick_rate
        self.running = True
        self.logger = get_logger("net.server")

        # Host player lives on the server process and is broadcast like any other player,
        # but has no associated network client.
        self.host_player_id = "host_player"
        self.player_states[self.host_player_id] = {
            "pos": [10, 2, 10],
            "rot_y": 0,
            "last_update": time.time(),
            "is_host": True,
        }
        
    async def start(self):
        """Start the TCP server."""
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        # Print the actual listening address
        addr = self.server.sockets[0].getsockname()
        self.logger.info(f"Server listening on {addr[0]}:{addr[1]}")
        self.logger.info(f"Other players can connect to your LAN IP at port {addr[1]}")
        
        # Start the broadcast task
        asyncio.create_task(self.broadcast_state_loop())
        
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""
        # Assign player ID
        player_id = f"player_{self.next_player_id}"
        self.next_player_id += 1
        
        # Store client writer
        self.clients[player_id] = writer
        
        # Initialize player state
        self.player_states[player_id] = {
            "pos": [10, 2, 10],  # Default spawn
            "rot_y": 0,
            "last_update": time.time()
        }
        
        # Send welcome message with player ID
        welcome_msg = json.dumps({
            "type": "welcome",
            "player_id": player_id,
            "spawn_pos": self.player_states[player_id]["pos"]
        }) + "\n"
        writer.write(welcome_msg.encode())
        await writer.drain()
        
        # Notify all clients about the new player
        await self.broadcast_player_join(player_id)
        
        self.logger.info(
            f"Player {player_id} connected from {writer.get_extra_info('peername')} | total_clients={len(self.clients)}"
        )
        
        try:
            # Process messages from this client
            while True:
                data = await reader.readline()
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode().strip())
                    await self.handle_message(player_id, message)
                except json.JSONDecodeError:
                    print(f"Invalid JSON from {player_id}")
                    
        except (ConnectionResetError, asyncio.CancelledError):
            pass
        finally:
            # Clean up on disconnect
            await self.handle_disconnect(player_id)
    
    async def handle_message(self, player_id: str, message: Dict):
        """Process incoming message from a client."""
        msg_type = message.get("type")
        
        if msg_type == "state_update":
            # Update player state
            if player_id in self.player_states:
                self.player_states[player_id].update({
                    "pos": message.get("pos", [0, 0, 0]),
                    "rot_y": message.get("rot_y", 0),
                    "last_update": time.time()
                })
        elif msg_type == "admin_command":
            command = message.get("command", "")
            await self.handle_admin_command(player_id, command)
        else:
            print(f"Unknown message type from {player_id}: {msg_type}")
    
    async def handle_disconnect(self, player_id: str):
        """Clean up when a client disconnects."""
        # Never remove the host player via disconnect logic.
        if player_id == self.host_player_id:
            return
        if player_id in self.clients:
            del self.clients[player_id]
        if player_id in self.player_states:
            del self.player_states[player_id]
        
        self.logger.info(f"Player {player_id} disconnected | total_clients={len(self.clients)}")
        
        # Notify other clients
        await self.broadcast_player_leave(player_id)
    
    async def broadcast_player_join(self, player_id: str):
        """Broadcast that a new player joined."""
        message = json.dumps({
            "type": "player_join",
            "player_id": player_id
        }) + "\n"
        
        await self.broadcast_to_all(message, exclude=None)
    
    async def broadcast_player_leave(self, player_id: str):
        """Broadcast that a player left."""
        message = json.dumps({
            "type": "player_leave",
            "player_id": player_id
        }) + "\n"
        
        await self.broadcast_to_all(message, exclude=None)
    
    async def broadcast_state_loop(self):
        """Periodically broadcast all player states to clients."""
        while self.running:
            start = time.perf_counter()
            await asyncio.sleep(self.tick_interval)
            await self.broadcast_state()
            loop_ms = (time.perf_counter() - start) * 1000.0
            log_metric(
                "server_tick_ms",
                loop_ms,
                labels={"players": len(self.player_states), "clients": len(self.clients)},
            )
    
    async def broadcast_state(self):
        """Broadcast current state of all players."""
        if not self.player_states:
            return
        
        message = json.dumps({
            "type": "state_snapshot",
            "players": self.player_states,
            "timestamp": time.time()
        }) + "\n"
        
        payload_bytes = len(message.encode("utf-8"))
        # Log human-readable timing at DEBUG level to avoid spamming the console,
        # but still record CSV metrics for performance analysis.
        with time_block(
            "server_broadcast_state",
            self.logger,
            {"players": len(self.player_states), "clients": len(self.clients), "bytes": payload_bytes},
            level=logging.DEBUG,
        ):
            await self.broadcast_to_all(message)
    
    async def broadcast_to_all(self, message: str, exclude: str = None):
        """Send a message to all connected clients."""
        disconnected = []
        
        for player_id, writer in self.clients.items():
            if exclude and player_id == exclude:
                continue
                
            try:
                writer.write(message.encode())
                await writer.drain()
            except (ConnectionResetError, BrokenPipeError):
                disconnected.append(player_id)
        
        # Clean up disconnected clients
        for player_id in disconnected:
            await self.handle_disconnect(player_id)

    async def send_admin_response(self, player_id: str, lines: List[str]) -> None:
        """Send admin command output back to a specific player."""
        if not lines:
            return
        writer = self.clients.get(player_id)
        if writer is None:
            return
        message = json.dumps({
            "type": "admin_response",
            "lines": lines,
        }) + "\n"
        try:
            writer.write(message.encode())
            await writer.drain()
        except (ConnectionResetError, BrokenPipeError):
            await self.handle_disconnect(player_id)

    async def handle_admin_command(self, player_id: str, command: str) -> None:
        """Execute an admin command string issued by a client player."""
        command = (command or "").strip()
        if not command:
            return

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
            players = self.list_players()
            if not players:
                lines.append("No players.")
            else:
                for pid, state in players.items():
                    tag = " (host)" if pid == self.host_player_id or state.get("is_host") else ""
                    pos = state.get("pos")
                    rot = state.get("rot_y")
                    lines.append(f"- {pid}{tag} pos={pos} rot_y={rot}")

        elif cmd == "/kick":
            if not args:
                lines.append("Usage: /kick <player_id>")
            else:
                pid = args[0]
                if pid == self.host_player_id:
                    lines.append("Cannot kick the host player.")
                else:
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
                    self.set_host_position(x, y, z)
                    lines.append(f"Host moved to ({x}, {y}, {z}).")
                except ValueError:
                    lines.append("Coordinates must be numbers.")

        elif cmd == "/hostrot":
            if len(args) != 1:
                lines.append("Usage: /hostrot yaw")
            else:
                try:
                    yaw = float(args[0])
                    self.set_host_rotation(yaw)
                    lines.append(f"Host rotation set to {yaw}.")
                except ValueError:
                    lines.append("Yaw must be a number.")

        elif cmd in {"/quit", "/exit", "/shutdown"}:
            lines.append("Shutting down server...")
            self.running = False
            if self.server is not None:
                self.server.close()

        else:
            lines.append(f"Unknown command: {cmd}. Try /help")

        await self.send_admin_response(player_id, lines)

    # --- Admin / host utilities ---

    def list_players(self) -> Dict[str, Dict]:
        """Return a snapshot of current players, including host."""
        return dict(self.player_states)

    async def kick_player(self, player_id: str) -> bool:
        """Disconnect a player by ID. Returns True if a player was kicked."""
        if player_id == self.host_player_id:
            return False

        writer = self.clients.get(player_id)
        if writer is None:
            return False

        try:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
        except Exception:
            pass

        await self.handle_disconnect(player_id)
        return True

    def set_host_position(self, x: float, y: float, z: float) -> None:
        """Move the host player to a new position."""
        state = self.player_states.get(self.host_player_id)
        if not state:
            return
        state["pos"] = [float(x), float(y), float(z)]
        state["last_update"] = time.time()
        self.logger.info(f"Host moved to pos={state['pos']}")

    def set_host_rotation(self, rot_y: float) -> None:
        """Rotate the host player around Y axis."""
        state = self.player_states.get(self.host_player_id)
        if not state:
            return
        state["rot_y"] = float(rot_y)
        state["last_update"] = time.time()
        self.logger.info(f"Host rotation set to rot_y={state['rot_y']}")


def get_lan_ip():
    """Get the LAN IP address for this machine."""
    try:
        # Create a socket to a non-existent address to find our local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


async def main():
    """Main entry point for the game server."""
    server = GameServer()
    lan_ip = get_lan_ip()
    
    print(f"MyCraft LAN Server")
    print(f"Local IP: {lan_ip}")
    print(f"Port: 5420")
    print(f"Tell family to connect to: {lan_ip}:5420")
    print("-" * 40)
    
    async def admin_console_loop() -> None:
        """Simple slash-command console for server admin / host player.

        Runs in parallel with the server and reads from stdin using a thread
        executor so it doesn't block the event loop.
        """
        loop = asyncio.get_running_loop()
        while True:
            try:
                line = await loop.run_in_executor(None, input, "server> ")
            except (EOFError, KeyboardInterrupt):
                print("\nConsole shutting down...")
                break

            line = line.strip()
            if not line:
                continue

            if not line.startswith("/"):
                print("Commands must start with '/'. Try /help")
                continue

            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in {"/quit", "/exit", "/shutdown"}:
                print("Shutting down server...")
                # Stop accepting new connections; existing clients will drop as server closes.
                if server.server is not None:
                    server.server.close()
                    await server.server.wait_closed()
                break

            elif cmd in {"/help", "/?"}:
                print("Available commands:")
                print("  /help                 Show this help")
                print("  /list                 List players (including host)")
                print("  /kick <player_id>     Disconnect a player")
                print("  /hostpos x y z        Move host player to position")
                print("  /hostrot yaw          Set host Y rotation in degrees")
                print("  /quit                 Shut down the server")

            elif cmd == "/list":
                players = server.list_players()
                if not players:
                    print("No players.")
                else:
                    for pid, state in players.items():
                        tag = " (host)" if pid == server.host_player_id or state.get("is_host") else ""
                        pos = state.get("pos")
                        rot = state.get("rot_y")
                        print(f"- {pid}{tag} pos={pos} rot_y={rot}")

            elif cmd == "/kick":
                if not args:
                    print("Usage: /kick <player_id>")
                    continue
                pid = args[0]
                if pid == server.host_player_id:
                    print("Cannot kick the host player.")
                    continue
                ok = await server.kick_player(pid)
                if ok:
                    print(f"Kicked {pid}.")
                else:
                    print(f"No such player: {pid}")

            elif cmd == "/hostpos":
                if len(args) != 3:
                    print("Usage: /hostpos x y z")
                    continue
                try:
                    x, y, z = map(float, args)
                except ValueError:
                    print("Coordinates must be numbers.")
                    continue
                server.set_host_position(x, y, z)

            elif cmd == "/hostrot":
                if len(args) != 1:
                    print("Usage: /hostrot yaw")
                    continue
                try:
                    yaw = float(args[0])
                except ValueError:
                    print("Yaw must be a number.")
                    continue
                server.set_host_rotation(yaw)

            else:
                print(f"Unknown command: {cmd}. Try /help")

        # When console loop exits, stop the server loop.
        raise KeyboardInterrupt

    try:
        await asyncio.gather(server.start(), admin_console_loop())
    except KeyboardInterrupt:
        print("\nServer shutting down...")


if __name__ == "__main__":
    asyncio.run(main())