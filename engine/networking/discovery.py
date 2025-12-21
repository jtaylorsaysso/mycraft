import socket
import json
import time
import threading
from dataclasses import dataclass
from typing import List, Optional

BROADCAST_PORT = 5421
BROADCAST_INTERVAL = 1.0
MAGIC_HEADER = b"MYCRAFT_DISCOVERY"

@dataclass
class DiscoveredServer:
    ip: str
    port: int
    name: str
    player_count: int
    max_players: int
    last_seen: float

class DiscoveryBroadcaster:
    """Broadcasts server presence over UDP."""
    def __init__(self, port: int, max_players: int):
        from engine.core.logger import get_logger
        
        self.server_port = port
        self.max_players = max_players
        self.running = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_thread = None
        self.logger = get_logger("net.discovery.broadcaster")
        self._last_error_log = 0  # Rate limit error logging

    def start(self, get_player_count_cb):
        self.running = True
        self.broadcast_thread = threading.Thread(
            target=self._broadcast_loop, 
            args=(get_player_count_cb,),
            daemon=True
        )
        self.broadcast_thread.start()

    def stop(self):
        self.running = False
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=1.0)
        self.sock.close()

    def _broadcast_loop(self, get_player_count_cb):
        while self.running:
            try:
                data = {
                    "port": self.server_port,
                    "players": get_player_count_cb(),
                    "max_players": self.max_players,
                    "name": f"MyCraft Server ({socket.gethostname()})"
                }
                payload = MAGIC_HEADER + json.dumps(data).encode("utf-8")
                
                # Send to global broadcast 
                try:
                    self.sock.sendto(payload, ('<broadcast>', BROADCAST_PORT))
                except OSError:
                    # Fallback for systems where <broadcast> fails or permissions deny it
                    self.sock.sendto(payload, ('255.255.255.255', BROADCAST_PORT))

                # Also send to localhost for single-machine testing reliability
                self.sock.sendto(payload, ('127.0.0.1', BROADCAST_PORT))
                
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                # Log broadcast errors but rate-limit to prevent spam (max once per 10s)
                now = time.time()
                if now - self._last_error_log > 10.0:
                    self.logger.warning(f"Broadcast error: {e}")
                    self._last_error_log = now
                time.sleep(BROADCAST_INTERVAL)

def find_servers(timeout: float = 2.0) -> List[DiscoveredServer]:
    """Listen for UDP broadcasts to find servers."""
    from engine.core.logger import get_logger
    logger = get_logger("net.discovery")
    
    found_servers = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow multiple listeners
    try:
        # Bind to all interfaces on the broadcast port
        sock.bind(('', BROADCAST_PORT))
        sock.settimeout(0.5)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                if data.startswith(MAGIC_HEADER):
                    json_data = data[len(MAGIC_HEADER):].decode("utf-8")
                    info = json.loads(json_data)
                    
                    server = DiscoveredServer(
                        ip=addr[0],
                        port=info['port'],
                        name=info.get('name', 'Unknown Server'),
                        player_count=info.get('players', 0),
                        max_players=info.get('max_players', 16),
                        last_seen=time.time()
                    )
                    # Key by IP:Port to avoid duplicates
                    key = f"{server.ip}:{server.port}"
                    found_servers[key] = server
            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {addr[0] if 'addr' in locals() else 'unknown'}: {e}")
            except UnicodeDecodeError as e:
                logger.warning(f"Invalid encoding from {addr[0] if 'addr' in locals() else 'unknown'}: {e}")
            except Exception as e:
                logger.error(f"Discovery recv error: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Discovery bind/setup error: {e}", exc_info=True)
    finally:
        sock.close()
        
    return list(found_servers.values())
