#!/usr/bin/env python3
"""
MyCraft LAN Client Entry Point

Connects to a MyCraft server for multiplayer on LAN.

Usage:
    python run_client.py --host 192.168.1.42 --port 5420
    python run_client.py --host localhost  # for local testing
    python run_client.py --preset creative  # Single player with god mode
    
Phase 2 Features:
    python run_client.py --config config/playtest.json  # Hot-reload config
    python run_client.py --record my_session  # Record input to recordings/my_session.json
    python run_client.py --replay recordings/my_session.json  # Replay a session
"""

import argparse
import sys
from pathlib import Path
from engine.game_app import run
from network.client import connect, disconnect


def main():
    parser = argparse.ArgumentParser(description="MyCraft LAN Client")
    parser.add_argument("--host", help="Server IP address or hostname (optional, defaults to Single Player)")
    parser.add_argument("--port", type=int, default=5420, help="Server port (default: 5420)")
    parser.add_argument("--sensitivity", type=float, default=40.0, help="Mouse sensitivity (default: 40.0)")
    
    # Playtest Presets
    parser.add_argument("--preset", choices=['creative', 'testing', 'performance'], help="Configuration preset")
    parser.add_argument("--god-mode", action="store_true", help="Enable flight and no collision")
    parser.add_argument("--debug", action="store_true", help="Show debug overlay")
    parser.add_argument("--spawn", nargs=3, type=float, metavar=('X', 'Y', 'Z'), help="Override spawn position: X Y Z")
    
    # Phase 2: Hot-Config & Session Recording
    parser.add_argument("--config", help="Path to JSON config file for hot-reload (default: config/playtest.json)")
    parser.add_argument("--record", metavar="NAME", help="Record session to recordings/<NAME>.json")
    parser.add_argument("--replay", metavar="FILE", help="Replay a recorded session file")
    
    args = parser.parse_args()
    
    # Default Configuration
    config = {
        'networking': False,
        'sensitivity': args.sensitivity,
        'god_mode': False,
        'debug': False,
        'spawn_point': None,
        'config_path': None,
        'record_session': None,
        'replay_session': None
    }
    
    # 1. Apply Preset
    if args.preset == 'creative':
        config['god_mode'] = True
        config['debug'] = True
        print("🎨 Loaded CREATIVE preset")
    elif args.preset == 'testing':
        config['debug'] = True
        print("🧪 Loaded TESTING preset")
    elif args.preset == 'performance':
        config['debug'] = False
        print("⚡ Loaded PERFORMANCE preset")
        
    # 2. Apply Explicit Flags (override presets)
    if args.god_mode:
        config['god_mode'] = True
    if args.debug:
        config['debug'] = True
    if args.spawn:
        config['spawn_point'] = tuple(args.spawn)
        print(f"📍 Spawn override: {config['spawn_point']}")
    
    # 3. Phase 2: Hot-Config
    if args.config:
        config['config_path'] = args.config
        print(f"⚙️ Hot-config: {args.config}")
    else:
        # Default config path if exists
        default_config = Path("config/playtest.json")
        if default_config.exists():
            config['config_path'] = str(default_config)
            print(f"⚙️ Hot-config (default): {default_config}")
    
    # 4. Phase 2: Session Recording
    if args.record:
        config['record_session'] = args.record
        print(f"🎬 Will record session: {args.record}")
    
    # 5. Phase 2: Session Replay
    if args.replay:
        config['replay_session'] = args.replay
        print(f"▶️ Will replay session: {args.replay}")

    try:
        if args.host:
            # Connect to server
            print(f"Connecting to {args.host}:{args.port}...")
            client = connect(args.host, args.port)
            
            if client.is_connected():
                print(f"Connected! Starting game...")
                config['networking'] = True
                run(**config)
            else:
                print("Failed to connect to server")
                sys.exit(1)
        else:
            print("Starting Single Player Mode...")
            run(**config)
            
    except ConnectionError as e:
        print(f"Connection error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        disconnect()


if __name__ == "__main__":
    main()