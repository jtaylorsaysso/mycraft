# MyCraft LAN Multiplayer Guide

## Overview

MyCraft supports LAN multiplayer through a TCP-based architecture. The system is designed for family/local play with minimal setup and no external dependencies.

## Architecture

### Server-Client Model

- **Server**: Authoritative game state, broadcasts player positions at 20 Hz
- **Client**: Sends local player state at 10 Hz, receives and renders remote players
- **Protocol**: JSON messages over TCP with newline delimiters

### Network Flow

```text
Client A                     Server                     Client B
    | ---- state_update ---> |                           |
    |                        | ---- state_snapshot ---> |
    |                        | <---- state_update ----   |
    | <--- state_snapshot -- |                           |
```

## Quick Start

### 1. Start Server

```bash
source .venv/bin/activate
python3 run_server.py
```

Output:

```text
MyCraft LAN Server
Local IP: 192.168.1.101
Port: 5420
Tell family to connect to: 192.168.1.101:5420
----------------------------------------
MyCraft server listening on 192.168.1.101:5420
```

### 2. Connect Clients

On each player's machine:

```bash
source .venv/bin/activate
python3 run_client.py --host 192.168.1.101 --port 5420
```

For local testing on the same machine:

```bash
python3 run_client.py --host localhost --port 5420
```

### 3. Firewall Setup

Ensure port 5420 is allowed:

```bash
sudo ufw allow 5420
sudo ufw enable
```

## Message Protocol

### Message Types

#### welcome

Server assigns player ID and spawn position:

```json
{
  "type": "welcome",
  "player_id": "player_1",
  "spawn_pos": [10, 2, 10]
}
```

#### state_update

Client sends position/rotation to server:

```json
{
  "type": "state_update",
  "pos": [10.5, 2.0, 10.2],
  "rot_y": 45.0
}
```

#### state_snapshot

Server broadcasts all player states:

```json
{
  "type": "state_snapshot",
  "players": {
    "player_1": {"pos": [10, 2, 10], "rot_y": 45},
    "player_2": {"pos": [12, 2, 8], "rot_y": 90}
  },
  "timestamp": 1699123456.789
}
```

#### player_join / player_leave
Connection notifications:
```json
{
  "type": "player_join",
  "player_id": "player_3"
}
```

## Network Settings

- **Port**: 5420 (configurable)
- **Server tick rate**: 20 Hz (state broadcasts)
- **Client send rate**: 10 Hz (position updates)
- **Timeout**: 5 seconds
- **Protocol**: TCP with newline-delimited JSON

## Player Representation

- **Local player**: Brown mannequin (3 stacked cubes)
- **Remote players**: Azure cubes (simple representation)
- **Position sync**: Real-time at 20 Hz
- **Rotation sync**: Y-axis rotation only

## Troubleshooting

### Connection Failed

1. **Check server is running**: `lsof -i :5420`
2. **Verify IP address**: Use server's displayed LAN IP
3. **Firewall**: Ensure port 5420 is allowed
4. **Network**: Ensure both machines are on same LAN

### Performance Issues

- **Network lag**: Check Wi-Fi signal strength
- **High latency**: Consider reducing tick rates
- **Packet loss**: Switch to wired connection if available

### Common Errors

- **"Address already in use"**: Kill existing server process
- **"Connection refused"**: Server not running or wrong IP
- **"Event loop closed"**: Normal on client shutdown

## Technical Details

### Server Implementation

- **Asyncio TCP server** on `0.0.0.0:5420`
- **Player state tracking** in memory dictionary
- **Broadcast task** runs at fixed 20 Hz interval
- **Connection cleanup** on disconnect

### Client Implementation

- **Background thread** with asyncio event loop
- **Thread-safe queues** for send/receive operations
- **Rate limiting** for outgoing messages (10 Hz)
- **Entity management** for remote players

### Integration Points

- **Player class**: Handles networking when `networking=True`
- **Game loop**: Calls `update_networking()` and `update_remote_players()`
- **Remote entities**: Created/destroyed dynamically

## Future Enhancements

### Planned Features

- **Player names** above heads
- **Chat system** (text messages)
- **Smoother interpolation** for remote movement
- **Player colors** customization
- **Spectator mode** for observers

### Technical Improvements

- **UDP protocol** for faster position updates
- **Entity interpolation** to smooth movement
- **Compression** for bandwidth optimization
- **Authentication** for private games

---

*Last Updated: 2025-11-22*
*Version: 1.0*
