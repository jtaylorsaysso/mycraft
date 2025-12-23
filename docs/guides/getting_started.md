# Getting Started with MyCraft

Welcome to MyCraft! This guide will get you from zero to playing in under 5 minutes.

---

## What is MyCraft?

MyCraft is a **beginner-friendly voxel game engine** for creating action-RPG adventures. Think exploring colorful vertical worlds with friends, mastering momentum-based movement, and overcoming challenges—all powered by a solid multiplayer foundation.

**Right now**, we're in pre-alpha playtest mode. You'll be playing `voxel_world`, our flagship game that demonstrates all the engine's capabilities.

---

## Who is This For?

- **Playtesters**: You want to try the game and give feedback
- **Beginners**: You're curious about game development but don't code (yet!)
- **Developers**: You want to see what MyCraft can do under the hood

---

## Step 1: Install Python

MyCraft requires **Python 3.12 or newer**.

### Check if You Have Python

Open your terminal (Mac/Linux) or Command Prompt (Windows) and run:

```bash
python3 --version
```

If you see `Python 3.12.x` or higher, you're good! Skip to Step 2.

### Install Python

**Windows**:

1. Download from [python.org/downloads](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation

**Mac**:

```bash
brew install python
```

**Linux (Ubuntu/Debian)**:

```bash
sudo apt install python3-full python3-pip
```

---

## Step 2: Download MyCraft

Clone or download the MyCraft repository to your computer.

If you have `git`:

```bash
git clone https://github.com/yourusername/mycraft.git
cd mycraft
```

Otherwise, download the ZIP file and extract it.

---

## Step 3: Install Dependencies

Open your terminal in the `mycraft` folder and run:

```bash
pip install -r requirements.txt
```

This installs Panda3D (the 3D engine) and other required libraries.

**Note**: This may take 1-2 minutes depending on your internet speed.

---

## Step 4: Launch the Game

### Using the Launcher (Recommended)

**Windows**: Double-click `launcher.py`

**Mac/Linux**:

```bash
./launcher.py
```

You'll see the MyCraft Launcher window with two columns:

- **Left**: Host a server for others to join
- **Right**: Join a game (single-player or multiplayer)

### Quick Start: Single Player

1. In the launcher, look at the **right column** ("Join a Game")
2. Enter your player name
3. Choose a preset (try **Creative** for flying around)
4. Click **🎮 PLAY SINGLE PLAYER**

The game window will open and you'll spawn into a procedurally generated world!

---

## Step 5: Explore and Play

### Controls

| Action | Key |
|--------|-----|
| **Move** | `W` `A` `S` `D` |
| **Look Around** | Mouse |
| **Jump** | `Space` |
| **Fly Up** (Creative) | `Space` |
| **Fly Down** (Creative) | `Shift` |
| **Unlock Mouse** | `Escape` |

### What to Try

- **Explore Biomes**: Walk around and discover plains, forests, deserts, mountains, canyons, rivers, beaches, and swamps
- **Test Physics**: Jump on slopes, swim in water, climb mountains
- **Creative Mode**: Press `G` to toggle god mode and fly around
- **Debug Info**: In Creative/Testing presets, you'll see FPS and position stats

---

## Step 6: Multiplayer (Optional)

Want to play with friends on the same WiFi?

### Host a Server

1. One person clicks **🚀 LAUNCH SERVER** (left column)
2. A terminal window opens running the server
3. Keep this window open while playing

### Join the Server

1. Other players open the launcher
2. Click **🔄 Refresh** in the "Discovered LAN Servers" section
3. Click on the server name in the list (it auto-fills the address)
4. Click **🌐 JOIN LAN SERVER**

Everyone spawns into the same world and can see each other!

---

## Troubleshooting

### "No servers found"

- Make sure the host clicked **LAUNCH SERVER** and the terminal is still open
- Click **Refresh** again
- Verify you're on the same WiFi network

### "The game is laggy"

- Close other apps (browsers, Spotify, etc.)
- Re-launch with the **Performance** preset
- Check the `logs/` folder for error messages

### "My mouse is stuck"

- Press `Escape` to unlock your cursor

### "Python not found"

- Make sure you checked "Add Python to PATH" during installation (Windows)
- Try `python3` instead of `python` in your commands

---

## What's Next?

Now that you're playing, here's what to explore:

1. **Give Feedback**: Found a bug? Have ideas? See [CONTRIBUTING.md](../CONTRIBUTING.md)
2. **Learn the Controls**: Check out the [Player Guide](../PLAYER_GUIDE.md) for advanced tips
3. **Customize Settings**: Edit `config/playtest.json` for hot-reload tuning
4. **Explore the Code**: Curious how it works? See [Documentation](index.md)

---

## For Playtesters

You're helping shape MyCraft! Here's how to be a great playtester:

### What We Need

- **Bug Reports**: If something breaks, tell us!
- **Gameplay Feedback**: Is it fun? Confusing? Too slow?
- **Performance Notes**: Does it run smoothly on your computer?
- **First Impressions**: Was setup easy? What was unclear?

### How to Report

1. **Record Your Session**: Check "Record" in the launcher before playing
2. **Take Screenshots**: Press your screenshot key when bugs happen
3. **Note Details**: What were you doing? Where were you?
4. **Share Files**: Send recordings from `recordings/` and logs from `logs/`

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed bug report guidelines.

---

## Quick Reference

| Task | Command |
|------|---------|
| Launch GUI | `./launcher.py` |
| Single Player | Click "PLAY SINGLE PLAYER" |
| Host Server | Click "LAUNCH SERVER" |
| Join Server | Click "JOIN LAN SERVER" |
| Manual Launch | `python run_client.py --preset creative` |

---

## Need Help?

- **Player Guide**: [PLAYER_GUIDE.md](../PLAYER_GUIDE.md)
- **Configuration**: [docs/PLAYTEST_CONFIG_GUIDE.md](PLAYTEST_CONFIG_GUIDE.md)
- **Technical Docs**: [docs/index.md](index.md)
- **Roadmap**: [ROADMAP.md](../ROADMAP.md)

---

**Welcome to MyCraft! Have fun exploring! 🎮**

*Last Updated: 2025-12-21*
