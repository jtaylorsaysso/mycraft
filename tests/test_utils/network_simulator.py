
import asyncio
import random
import time
from typing import Optional, List

class NetworkSimulator:
    """Simulates network conditions for testing."""
    def __init__(self, latency_ms: int = 0, jitter_ms: int = 0, packet_loss_pct: float = 0.0):
        self.latency_ms = latency_ms
        self.jitter_ms = jitter_ms
        self.packet_loss_pct = packet_loss_pct

    def should_drop_packet(self) -> bool:
        """Determines if a packet should be dropped based on loss percentage."""
        if self.packet_loss_pct <= 0:
            return False
        return random.random() * 100 < self.packet_loss_pct

    async def delay_packet(self):
        """Waits for the simulated latency period."""
        if self.latency_ms <= 0 and self.jitter_ms <= 0:
            return

        delay = self.latency_ms
        if self.jitter_ms > 0:
            delay += random.randint(-self.jitter_ms, self.jitter_ms)
        
        delay = max(0, delay) # Ensure non-negative
        if delay > 0:
            await asyncio.sleep(delay / 1000.0)

class LatencyStreamWriter:
    """Wraps an asyncio.StreamWriter to inject latency and packet loss."""
    def __init__(self, writer: asyncio.StreamWriter, simulator: NetworkSimulator):
        self.writer = writer
        self.simulator = simulator

    def write(self, data: bytes):
        if self.simulator.should_drop_packet():
            return # Drop silently
        
        # We can't easily await in a synchronous write method.
        # So we just pass it through for now, but in a real scenario we'd need
        # to queue it or use an async write method if the API supported it.
        # However, asyncio.StreamWriter.write is non-blocking (sync).
        # To simulate latency on WRITE, we might need a different approach or 
        # sleep before calling writes in the test client.
        
        # Alternatively, we can assume latency applies to transmission time, 
        # so drain() is where we wait? drain() is async.
        self.writer.write(data)

    async def drain(self):
        await self.simulator.delay_packet()
        await self.writer.drain()
    
    def close(self):
        self.writer.close()
        
    async def wait_closed(self):
        await self.writer.wait_closed()
        
    def get_extra_info(self, name, default=None):
        return self.writer.get_extra_info(name, default)

