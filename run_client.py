#!/usr/bin/env python3
"""
MyCraft LAN Client Entry Point

Connects to a MyCraft server for multiplayer on LAN.

Usage:
    python run_client.py --host 192.168.1.42 --port 5420
    python run_client.py --host localhost  # for local testing
"""

import argparse
import sys
from engine.game_app import run
from network.client import connect, disconnect


def main():
    parser = argparse.ArgumentParser(description="MyCraft LAN Client")
    parser.add_argument("--host", help="Server IP address or hostname (optional, defaults to Single Player)")
    parser.add_argument("--port", type=int, default=5420, help="Server port (default: 5420)")
    parser.add_argument("--sensitivity", type=float, default=40.0, help="Mouse sensitivity (default: 40.0)")
    
    args = parser.parse_args()
    
    try:
        if args.host:
            # Connect to server
            print(f"Connecting to {args.host}:{args.port}...")
            client = connect(args.host, args.port)
            
            if client.is_connected():
                print(f"Connected! Starting game...")
                # Run the game with networking enabled
                run(networking=True, sensitivity=args.sensitivity)
            else:
                print("Failed to connect to server")
                sys.exit(1)
        else:
            print("Starting Single Player Mode...")
            run(networking=False, sensitivity=args.sensitivity)
            
    except ConnectionError as e:
        print(f"Connection error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        disconnect()


if __name__ == "__main__":
    main()