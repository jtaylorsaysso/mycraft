# MyCraft Playtest Quickstart

Welcome to the MyCraft playtest! 

> [!TIP]
> **New for Playtesters:** Use the **GUI Launcher**!
> Run: `./launcher.py` (or double-click it) to join easily without terminal commands.
> See [PLAYER_GUIDE.md](PLAYER_GUIDE.md) for details.

## 🚀 Speed Run (For Developers)

One command to rule them all (restarts server + 1 client):
```bash
./restart_playtest.sh
```

Restart with 2 clients:
```bash
./restart_playtest.sh --clients 2
```

## 🎮 How to Join

### 1. Start the Server
Open a terminal and run:
```bash
python run_server.py
```
*Optional: `python run_server.py --broadcast-rate 60 --debug` for high-performance logging.*

### 2. Start the Client
Open a NEW terminal and run:
```bash
python run_client.py --host localhost
```

### 3. Cheat Codes (Presets)
Use these presets to jump straight into specific testing modes:

- **Creative Mode** (Fly, no collision, debug stats):
  ```bash
  python run_client.py --host localhost --preset creative
  ```

- **Testing Mode** (Debug stats only):
  ```bash
  python run_client.py --host localhost --preset testing
  ```

- **God Mode Toggle**:
  Press **G** (if enabled) or start with `--god-mode`.
  - **Space**: Fly Up
  - **Shift**: Fly Down
  - **WASD**: Move (faster flying)

## 🔧 Phase 2: Advanced Playtest Features

### Hot-Reload Configuration
Edit settings while playing - no restart needed!
```bash
python run_client.py --config config/playtest.json --debug
```
Then edit `config/playtest.json` to change:
- `mouse_sensitivity` (default: 40.0)
- `movement_speed` (default: 6.0)
- `fly_speed` (default: 12.0)
- `jump_height` (default: 3.5)
- `god_mode` (true/false)

Changes apply within 1 second.

### Session Recording
Record your playtests for bug reproduction:
```bash
python run_client.py --record my_test_session --debug
```
Recording saves to `recordings/my_test_session.json` when you exit.

### Session Replay
Replay a recorded session:
```bash
python run_client.py --replay recordings/my_test_session.json
```

### Quick Commands (Debug Mode)
Press number keys 1-6 for quick playtest commands:
- **1**: `/help` - Show all commands
- **2**: `/info` - Current position/stats
- **3**: `/god` - Toggle god mode
- **4**: `/spawn` - Return to spawn
- **5**: `/speed 2` - Double speed
- **6**: `/speed 1` - Normal speed

## 🛠️ Troubleshooting

**"Connection Refused"**
- The server isn't running. Check your server terminal.
- Ensure you used `--host localhost` (or the correct LAN IP if testing across machines).

**"Mouse is stuck"**
- Press **Escape** to unlock your mouse cursor.

**"Lag / Stuttering"**
- The server might be overloaded. Try `run_client.py` with `--preset performance`.
- Check `logs/` for error messages.

## 🐛 How to Report Bugs

1. **Record a session** with `--record bug_report`.
2. Take a screenshot (Print Screen).
3. Note your **Chunk Coordinate** (visible in Creative/Testing preset).
4. Grab the latest log file from `logs/`.
5. Send session file + log + screenshot to James.

## ⌨️ All Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/info` | Current session info |
| `/tp <x> <y> <z>` | Teleport to position |
| `/speed <mult>` | Speed multiplier (0.5-5.0) |
| `/god` | Toggle god mode |
| `/spawn` | Return to spawn |
| `/sensitivity <val>` | Change mouse sensitivity |
| `/list` | List connected players |
| `/kick <player>` | Remove a player |

