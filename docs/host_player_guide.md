# Host Player Guide

This guide explains the host player feature and how to use the in-client admin console to manage a LAN game.

## Overview

MyCraft includes a logical “host player” that lives on the server and is visible to all clients. It does not have a network client of its own; it’s controlled only via admin commands from any connected client.

## In-Client Admin Console

### Opening the Console

- Press the `/` key in-game.
- A text input appears at the bottom of the screen.
- Mouse unlocks and movement pauses while the console is open.
- Press Enter to send a command; press `/` again to close the console.
- Recent command output appears in a small scrollback above the input.

### Available Commands

| Command | Description |
|---------|-------------|
| `/help` or `/?` | List all available commands |
| `/list` | Show all connected players, including the host player |
| `/kick <player_id>` | Disconnect a player (cannot kick the host player) |
| `/hostpos x y z` | Move the host player to the specified position |
| `/hostrot yaw` | Set the host player’s Y rotation (degrees) |
| `/quit` | Shut down the server (ends the game for everyone) |

### Example Usage

```text
/list
> - host_player (host) pos=[10, 2, 10] rot_y=0
> - player_1 pos=[10.2, 2, 10.1] rot_y=45

/hostpos 12 2 8
> Host moved to (12.0, 2.0, 8.0).

/kick player_2
> Kicked player_2.
```

## Host Player Details

- **Entity ID**: `host_player`
- **Appearance**: Azure cube, same size as remote players
- **Network**: No TCP client; state is updated only via admin commands
- **Persistence**: Exists as soon as the server starts; removed on shutdown
- **Visibility**: Included in `state_snapshot` broadcasts to all clients

### Why Have a Host Player?

- **Testing**: Move a non-player entity around to verify sync and rendering.
- **Staging**: Place a reference point for map features or events.
- **Future features**: Could become a “world admin” avatar with special permissions.

## Server-Side Console (Optional)

The server process also provides a stdin console with the same commands. This can be used for headless administration when no client is connected.

- Start server: `python run_server.py`
- At the `server>` prompt, type commands like `/list`, `/kick`, `/quit`

## Security Notes

- Any connected client can issue admin commands.
- There is no authentication or permission system yet.
- For trusted LAN use only. Future versions may add host-only commands or password protection.

## Troubleshooting

### Console Doesn’t Open

- Ensure you are connected to a server (`networking=True`).
- Press `/` (slash) key; ensure no other UI is capturing input.

### Commands Fail

- Verify command spelling and arguments.
- Use `/help` to see the current command list.
- Check the server log for errors.

### Host Player Not Visible

- The host player appears as an azure cube at `[10, 2, 10]` by default.
- Use `/list` to confirm it exists.
- Move it with `/hostpos` if it’s out of view.

---

*Last Updated: 2025-11-22*
