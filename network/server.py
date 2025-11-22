import asyncio
import json
import socket
from typing import Dict, Set
import time


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
        
    async def start(self):
        """Start the TCP server."""
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        # Print the actual listening address
        addr = self.server.sockets[0].getsockname()
        print(f"MyCraft server listening on {addr[0]}:{addr[1]}")
        print(f"Other players can connect to your LAN IP at port {addr[1]}")
        
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
        
        print(f"Player {player_id} connected from {writer.get_extra_info('peername')}")
        
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
        else:
            print(f"Unknown message type from {player_id}: {msg_type}")
    
    async def handle_disconnect(self, player_id: str):
        """Clean up when a client disconnects."""
        if player_id in self.clients:
            del self.clients[player_id]
        if player_id in self.player_states:
            del self.player_states[player_id]
        
        print(f"Player {player_id} disconnected")
        
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
        while True:
            await asyncio.sleep(self.tick_interval)
            await self.broadcast_state()
    
    async def broadcast_state(self):
        """Broadcast current state of all players."""
        if not self.player_states:
            return
        
        message = json.dumps({
            "type": "state_snapshot",
            "players": self.player_states,
            "timestamp": time.time()
        }) + "\n"
        
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
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")


if __name__ == "__main__":
    asyncio.run(main())