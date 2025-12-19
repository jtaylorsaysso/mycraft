#!/usr/bin/env python3
"""
MyCraft LAN Server Entry Point

Starts the TCP server for LAN multiplayer on port 5420.
Family members can connect using your LAN IP address.

Usage:
    python run_server.py
"""

import asyncio
from engine.networking.server import main


if __name__ == "__main__":
    asyncio.run(main())