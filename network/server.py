import asyncio
import json
import socket
from typing import Dict, Set, List
import time
import logging


from util.logger import get_logger, time_block, log_metric
from network.player_manager import PlayerManager
from network.commands import CommandProcessor
from network.discovery import DiscoveryBroadcaster


import argparse

class GameServer:
    """Simple TCP server for LAN multiplayer on port 5420."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5420, broadcast_rate: int = 20, max_players: int = 16, debug: bool = False):
        self.host = host
        self.port = port
        self.broadcast_rate = broadcast_rate
        self.max_players = max_players
        self.debug_mode = debug
        
        self.server = None
        self.clients: Dict[str, asyncio.StreamWriter] = {}
        
        self.player_manager = PlayerManager()
        self.command_processor = CommandProcessor(self, self.player_manager)
        
        # Initialize discovery
        self.discovery = DiscoveryBroadcaster(port, max_players)

        self.tick_rate = broadcast_rate  # Broadcast state X times per second
        self.tick_interval = 1.0 / self.tick_rate
        self.running = True
        self.logger = get_logger("net.server")
        
        if self.debug_mode:
            self.logger.setLevel(logging.DEBUG)
        
        # Identify host player ID for reference
        self.host_player_id = self.player_manager.host_player_id
        
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
        self.logger.info(f"Config: rate={self.broadcast_rate}Hz, max_players={self.max_players}, debug={self.debug_mode}")
        
        # Start the broadcast task
        asyncio.create_task(self.broadcast_state_loop())
        
        # Start discovery broadcasting
        self.discovery.start(lambda: len(self.clients))
        self.logger.info("LAN Discovery broadcasting started")
        
        async with self.server:

            await self.server.serve_forever()
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""
        # Assign player ID
        player_id = self.player_manager.generate_player_id()
        
        # Store client writer
        self.clients[player_id] = writer
        
        # Initialize player state
        self.player_manager.add_player(player_id)
        
        # Send welcome message with player ID
        welcome_msg = json.dumps({
            "type": "welcome",
            "player_id": player_id,
            "spawn_pos": self.player_manager.get_player_state(player_id)["pos"]
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
            self.player_manager.update_player_state(
                player_id,
                message.get("pos", [0, 0, 0]),
                message.get("rot_y", 0)
            )
        elif msg_type == "admin_command":
            command = message.get("command", "")
            lines = await self.command_processor.process_command(player_id, command)
            await self.send_admin_response(player_id, lines)
        else:
            print(f"Unknown message type from {player_id}: {msg_type}")
    
    async def handle_disconnect(self, player_id: str):
        """Clean up when a client disconnects."""
        # Never remove the host player via disconnect logic.
        if player_id == self.host_player_id:
            return
        if player_id in self.clients:
            del self.clients[player_id]
        
        self.player_manager.remove_player(player_id)
        
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
                labels={"players": len(self.player_manager.player_states), "clients": len(self.clients)},
            )
    
    async def broadcast_state(self):
        """Broadcast current state of all players."""
        players = self.player_manager.get_all_players()
        if not players:
            return
        
        message = json.dumps({
            "type": "state_snapshot",
            "players": players,
            "timestamp": time.time()
        }) + "\n"
        
        payload_bytes = len(message.encode("utf-8"))
        # Log human-readable timing at DEBUG level to avoid spamming the console,
        # but still record CSV metrics for performance analysis.
        with time_block(
            "server_broadcast_state",
            self.logger,
            {"players": len(players), "clients": len(self.clients), "bytes": payload_bytes},
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

    # --- Admin / host utilities ---

    # Most logic moved to CommandProcessor, but server needs to send responses.


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
    parser = argparse.ArgumentParser(description="MyCraft LAN Server")
    parser.add_argument("--broadcast-rate", type=int, default=20, help="State broadcast rate in Hz (default: 20)")
    parser.add_argument("--max-players", type=int, default=16, help="Max concurrent connections (default: 16)")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    server = GameServer(
        broadcast_rate=args.broadcast_rate,
        max_players=args.max_players,
        debug=args.debug
    )
    lan_ip = get_lan_ip()
    
    print(f"MyCraft LAN Server")
    print(f"Local IP: {lan_ip}")
    print(f"Port: 5420")
    print(f"Config: rate={args.broadcast_rate}Hz, players={args.max_players}, debug={args.debug}")
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
            except EOFError:
                print("\n[INFO] Admin console stdin closed (background mode). Server continuing...")
                # Keep the task alive but do nothing, so we don't trigger shutdown
                try:
                    while True:
                        await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    break
            except KeyboardInterrupt:
                print("\nConsole shutting down...")
                break

            line = line.strip()
            if not line:
                continue

            if not line.startswith("/"):
                print("Commands must start with '/'. Try /help")
                continue

            # Process command using the same processor as network clients
            # We use host_player_id as the issuer
            lines = await server.command_processor.process_command(server.host_player_id, line)
            for l in lines:
                print(l)

        # When console loop exits (via KeyboardInterrupt), stop the server loop.
        raise KeyboardInterrupt

    try:
        await asyncio.gather(server.start(), admin_console_loop())
    except KeyboardInterrupt:
        print("\nServer shutting down...")


if __name__ == "__main__":
    asyncio.run(main())