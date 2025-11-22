import asyncio
import json
import threading
import time
from typing import Dict, Callable, Optional, Any
from queue import Queue, Empty

from util.logger import get_logger, log_metric
class GameClient:
    """TCP client for connecting to MyCraft LAN server."""
    
    def __init__(self, host: str, port: int = 5420):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.player_id: Optional[str] = None
        
        # Thread-safe queues for async/sync communication
        self.send_queue = Queue()
        self.receive_queue = Queue()
        
        # Event loop running in background thread
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        
        # Callbacks for different message types
        self.callbacks: Dict[str, Callable] = {
            "welcome": self._handle_welcome,
            "state_snapshot": self._handle_state_snapshot,
            "player_join": self._handle_player_join,
            "player_leave": self._handle_player_leave,
        }
        
        # Current state of remote players
        self.remote_players: Dict[str, Dict] = {}

        # Telemetry
        self.logger = get_logger("net.client")
        self._sent_updates = 0
        self._received_snapshots = 0
        self._last_stats_time = time.time()
        
    def start(self):
        """Start the client in a background thread."""
        if self.thread and self.thread.is_alive():
            return
        
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        
        # Wait for connection
        for _ in range(50):  # 5 second timeout
            if self.connected:
                return
            time.sleep(0.1)
        
        raise ConnectionError(f"Failed to connect to {self.host}:{self.port}")
    
    def stop(self):
        """Stop the client."""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=1.0)
        self.connected = False
    
    def _run_event_loop(self):
        """Run the asyncio event loop in a background thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._async_start())
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.loop.close()
    
    async def _async_start(self):
        """Async connection and message handling."""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.connected = True
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
            
            # Start send and receive tasks
            send_task = asyncio.create_task(self._send_loop())
            receive_task = asyncio.create_task(self._receive_loop())
            
            # Wait for tasks to complete (they run until disconnect)
            await asyncio.gather(send_task, receive_task)
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.connected = False
    
    async def _send_loop(self):
        """Send messages from the queue to the server."""
        while self.connected and self.writer:
            try:
                # Get message from queue (with timeout to allow checking connection)
                message = await self.loop.run_in_executor(
                    None, lambda: self.send_queue.get(timeout=0.1)
                )
                
                if message:
                    data = json.dumps(message) + "\n"
                    self.writer.write(data.encode())
                    await self.writer.drain()
                    
            except Empty:
                continue
            except Exception as e:
                print(f"Send error: {e}")
                break
    
    async def _receive_loop(self):
        """Receive messages from the server and put them in the receive queue."""
        while self.connected and self.reader:
            try:
                data = await self.reader.readline()
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode().strip())
                    await self.loop.run_in_executor(
                        None, self.receive_queue.put, message
                    )
                    
                    # Handle immediate callbacks
                    msg_type = message.get("type")
                    if msg_type in self.callbacks:
                        await self.loop.run_in_executor(
                            None, self.callbacks[msg_type], message
                        )
                        
                except json.JSONDecodeError:
                    self.logger.warning("Invalid JSON from server")
                    
            except Exception as e:
                self.logger.error(f"Receive error: {e}")
                break
        
        self.connected = False
    
    def _handle_welcome(self, message: Dict):
        """Handle welcome message from server."""
        self.player_id = message.get("player_id")
        spawn_pos = message.get("spawn_pos", [10, 2, 10])
        self.logger.info(f"Welcome as {self.player_id}, spawn_pos={spawn_pos}")
    
    def _handle_state_snapshot(self, message: Dict):
        """Handle state snapshot from server."""
        players = message.get("players", {})
        timestamp = message.get("timestamp", time.time())
        
        # Update remote players (excluding self)
        for player_id, state in players.items():
            if player_id != self.player_id:
                self.remote_players[player_id] = {
                    **state,
                    "last_update": timestamp
                }
        
        # Remove players that are no longer in the snapshot
        current_ids = set(players.keys())
        for player_id in list(self.remote_players.keys()):
            if player_id not in current_ids:
                del self.remote_players[player_id]

        # Telemetry: count snapshots and remote players
        self._received_snapshots += 1
        now = time.time()
        if now - self._last_stats_time >= 5.0:
            log_metric(
                "client_remote_players",
                float(len(self.remote_players)),
                labels={"host": self.host, "port": self.port},
            )
            log_metric(
                "client_snapshots_per_s",
                self._received_snapshots / (now - self._last_stats_time),
                labels={"host": self.host, "port": self.port},
            )
            self._received_snapshots = 0
            self._last_stats_time = now
    
    def _handle_player_join(self, message: Dict):
        """Handle player join notification."""
        player_id = message.get("player_id")
        print(f"Player {player_id} joined the game")
    
    def _handle_player_leave(self, message: Dict):
        """Handle player leave notification."""
        player_id = message.get("player_id")
        if player_id in self.remote_players:
            del self.remote_players[player_id]
        print(f"Player {player_id} left the game")
    
    def send_state_update(self, pos: list, rot_y: float):
        """Send player state update to server."""
        if not self.connected:
            return
        
        message = {
            "type": "state_update",
            "pos": pos,
            "rot_y": rot_y
        }
        self.send_queue.put(message)
        self._sent_updates += 1

    
    def get_remote_players(self) -> Dict[str, Dict]:
        """Get current state of remote players."""
        return self.remote_players.copy()
    
    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        return self.connected and self.player_id is not None


# Singleton client instance for the game
_client_instance: Optional[GameClient] = None


def connect(host: str, port: int = 5420) -> GameClient:
    """Connect to a MyCraft server and return the client instance."""
    global _client_instance
    
    if _client_instance and _client_instance.is_connected():
        _client_instance.stop()
    
    _client_instance = GameClient(host, port)
    _client_instance.start()
    return _client_instance


def get_client() -> Optional[GameClient]:
    """Get the current client instance."""
    return _client_instance


def disconnect():
    """Disconnect from the server."""
    global _client_instance
    if _client_instance:
        _client_instance.stop()
        _client_instance = None