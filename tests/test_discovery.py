import pytest
import time
import socket
from network.discovery import DiscoveryBroadcaster, find_servers, BROADCAST_PORT

def test_discovery_flow():
    # Setup: Start a broadcaster
    test_port = 55555
    max_players = 10
    
    broadcaster = DiscoveryBroadcaster(test_port, max_players)
    broadcaster.start(get_player_count_cb=lambda: 5)
    
    try:
        # Give it a moment to send at least one packet
        time.sleep(0.5)
        
        # Act: Try to find servers
        # We need a longer timeout because the broadcast interval is 2.0s
        # But for test speed, we might want to monkeypatch the interval, 
        # or just wait up to 2.5s.
        servers = find_servers(timeout=2.5)
        
        # Assert
        found_myself = False
        for server in servers:
            # We check if we found the server we just started.
            # Local IP might match what discovery sees.
            if server.port == test_port and server.max_players == max_players:
                found_myself = True
                assert server.player_count == 5
                assert "MyCraft Server" in server.name
                break
        
        assert found_myself, "Failed to discover local broadcaster"
        
    finally:
        broadcaster.stop()
