# 🎮 MyCraft Player Guide

Welcome to the MyCraft Playtest! This guide will help you get set up and playing in seconds.

## 🚀 How to Play

### 1. Start the Launcher

Double-click `launcher.py` (or run it from your terminal). You'll see the MyCraft Launcher window.

### 2. Find a Server

Look at the **"Discovered LAN Servers"** list at the bottom.

- If you see a server, **click it**! The address will automatically be filled in.
- If the list is empty, make sure you (or your friend) are running the server on the same WiFi network.

### 3. Choose Your Style

Pick a **Preset** that fits how you want to play:

- **🎨 Creative**: Fly around, no collisions. Best for exploring.
- **🧪 Testing**: Normal gameplay with debug stats.
- **⚡ Performance**: Optimized for older computers.

### 4. Click LAUNCH

The game window will open, and you'll spawn into the world.

---

## 🕹️ Controls

### Movement & Camera

| Action | Key |
| :--- | :--- |
| **Move** | `W` `A` `S` `D` |
| **Look** | Mouse |
| **Jump** | `Space` |
| **Crouch / Dodge** | `Shift` (context-sensitive) |
| **Toggle Camera View** | `V` |

### Combat

| Action | Key |
| :--- | :--- |
| **Attack** | `Left Click` (Mouse 1) |
| **Parry** | `Right Click` (Mouse 2) |

### UI & Utilities

| Action | Key |
| :--- | :--- |
| **Pause Menu / Unlock Mouse** | `Escape` |
| **Toggle Debug Info** | `F3` |
| **Screenshot** | `F9` |

> **Note**: Your mouse will be locked to the game window when playing. Press **Escape** at any time to unlock your cursor and access the menu.

### 📷 Camera Modes

- **Third-Person (Default)**: See your character from behind. Great for exploring and seeing your animations.
- **First-Person**: Classic FPS view. Press `V` to toggle between modes.

### 🦸 God Mode (Creative Mode)

- **Toggle God Mode**: Edit `config/playtest.json` and set `"god_mode": true`, or use in-game settings menu
- **Fly Up**: `Space`
- **Fly Down**: `Shift`
- **Fly Faster**: Hold `W` while flying

---

## 🔧 Troubleshooting

### "I don't see any servers!"

- Click the **Refresh** button.
- Check that the server computer is turned on and running `run_server.py`.
- Ensure you are both on the **same WiFi network**.

### "The game is laggy"

- Close other apps (Chrome, Spotify).
- Re-launch the game using the **Performance** preset.

### "My mouse is stuck in the game!"

- Press **Escape** to unlock your mouse cursor and access the menu.

---

## 🐛 Found a Bug?

We love bug reports!

1. Check the **"Record Session"** box in the launcher before playing.
2. Press **F2** (or your screenshot key) to take a picture when the bug happens.
3. Tell James what you were doing.
4. The game will save a recording file (e.g., `Player_123456.json`) in the `recordings/` folder. Send this file + log + screenshot to James.
