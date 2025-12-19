import asyncio
import json
import threading
import time
from typing import Dict, Callable, Optional, Any, List
from queue import Queue, Empty

from engine.core.logger import get_logger, log_metric
class GameClient:
    """TCP client for connecting to MyCraft LAN server."""
    
    def __init__(self, host: str, port: int = 5420, max_reconnect_attempts: int = 3, connection_timeout: float = 10.0):
        self.host = host
        self.port = port
        self.max_reconnect_attempts = max_reconnect_attempts
        self.connection_timeout = connection_timeout
        
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.connecting = False
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
            "chat": self._handle_chat_message,
            "state_snapshot": self._handle_state_snapshot,
            "player_join": self._handle_player_join,
            "player_leave": self._handle_player_leave,
            "admin_response": self._handle_admin_response,
            "block_update": self._handle_block_update,
        }
        
        # Connection callbacks
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[Optional[Exception]], None]] = None
        self.on_connection_failed: Optional[Callable[[Exception], None]] = None
        self.on_block_update: Optional[Callable[[Dict], None]] = None
        
        # Current state of remote players
        self.remote_players: Dict[str, Dict] = {}

        # Admin console log (text lines)
        self._admin_log: List[str] = []

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
        # We wait a bit longer than the timeout to allow for retries
        max_wait = self.connection_timeout * self.max_reconnect_attempts * 2 
        start_time = time.time()
        
        while self.connecting or (self.thread.is_alive() and not self.connected):
            if self.connected:
                return
            if time.time() - start_time > max_wait:
                break
            time.sleep(0.1)
        
        if self.connected:
            return

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
        """Async connection and message handling with retry logic."""
        if not await self._connect_with_retry():
            return

        try:
            # Start send and receive tasks
            send_task = asyncio.create_task(self._send_loop())
            receive_task = asyncio.create_task(self._receive_loop())
            
            # Wait for tasks to complete (they run until disconnect)
            await asyncio.gather(send_task, receive_task)
            
        except Exception as e:
            self.logger.error(f"Client loop error: {e}")
            self.connected = False
    
    async def _connect_with_retry(self) -> bool:
        """Attempt to connect with exponential backoff."""
        attempt = 0
        self.connecting = True
        
        while attempt < self.max_reconnect_attempts:
            try:
                attempt += 1
                self.logger.info(f"Connecting to {self.host}:{self.port} (Attempt {attempt}/{self.max_reconnect_attempts})...")
                
                # Connection with timeout
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self.connection_timeout
                )
                
                self.connected = True
                self.connecting = False
                self.logger.info(f"Connected to server at {self.host}:{self.port}")
                
                if self.on_connected:
                   # Execute callback in thread-safe way if needed, 
                   # but here we are in the async loop
                   self.on_connected()
                
                return True
                
            except (ConnectionRefusedError, OSError, asyncio.TimeoutError) as e:
                self.logger.warning(f"Connection attempt {attempt} failed: {e}")
                
                if attempt < self.max_reconnect_attempts:
                    # Exponential backoff: 1s, 2s, 4s...
                    wait_time = 1.0 * (2 ** (attempt - 1))
                    self.logger.info(f"Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Max connection attempts reached. Giving up.")
                    if self.on_connection_failed:
                        self.on_connection_failed(e)
        
        self.connecting = False
        return False
    
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
                if self.on_disconnected:
                    self.on_disconnected(e)
                break
        
        self.connected = False
        if self.on_disconnected and self.reader: # Only trigger if we were seemingly connected
             # We check self.reader to avoid double triggering if exception block handled it
             # But simplistic check: if we break loop naturally
             pass
        
        # Ensure we mark as disconnected
        if self.connected: 
             self.connected = False
             if self.on_disconnected:
                 self.on_disconnected(None)
    
    def _handle_welcome(self, message: Dict):
        """Handle welcome message from server."""
        self.player_id = message.get("player_id")
        self.spawn_pos = message.get("spawn_pos", [10, 2, 10])
        self.logger.info(f"Welcome as {self.player_id}, spawn_pos={self.spawn_pos}")
    
        self.logger.info(f"Welcome as {self.player_id}, spawn_pos={self.spawn_pos}")
    
    def _handle_chat_message(self, message: Dict):
        """Handle chat message."""
        username = message.get("username", "Unknown")
        text = message.get("message", "")
        player_id = message.get("player_id")
        
        if self.on_chat_message:
            self.on_chat_message(username, text)
            
    def _handle_block_update(self, message: Dict):
        """Handle block update message."""
        pos = message.get("pos")
        block_type = message.get("block_type")
        
        # Telemetry
        # self.logger.debug(f"Block update: {pos} -> {block_type}")
        
        if self.on_block_update:
            self.on_block_update({
                "position": pos,
                "block_type": block_type
            })
            
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
    
    def _handle_admin_response(self, message: Dict):
        """Handle admin console output from server."""
        lines = message.get("lines", []) or []
        for line in lines:
            text = str(line)
            self._admin_log.append(text)
            self.logger.info(f"ADMIN: {text}")
    
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
        self.send_queue.put(message)
        self._sent_updates += 1

    def send_name(self, name: str):
        """Send player name to server."""
        if not self.connected:
            return
        
        message = {
            "type": "set_name",
            "name": name
        }
        self.send_queue.put(message)

    def send_admin_command(self, command: str) -> None:
        """Send an admin command string to the server."""
        if not self.connected:
            return
        command = (command or "").strip()
        if not command:
            return
        message = {
            "type": "admin_command",
            "command": command,
        }
        self.send_queue.put(message)

    def get_admin_log(self) -> List[str]:
        """Get a copy of the current admin console log lines."""
        return list(self._admin_log)

    
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