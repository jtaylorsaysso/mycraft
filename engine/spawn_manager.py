"""Cooperative multiplayer spawn management system.

Handles player spawning with proximity-based placement, spawn protection,
and multi-tier fallback logic for safe spawn locations.
"""

import random
import math
from typing import Optional, Tuple, List
from panda3d.core import LVector3f


class SpawnManager:
    """Manages player spawn locations for cooperative multiplayer.
    
    Spawn Priority:
    1. Near existing players (within min/max distance)
    2. Safe biome location
    3. Designated safe zone
    4. World spawn (fallback)
    """
    
    # Safe biomes for spawning
    SAFE_BIOMES = ["plains", "forest", "beach", "desert"]
    
    def __init__(self, world_spawn: Tuple[float, float, float] = (0, 0, 10)):
        """Initialize spawn manager.
        
        Args:
            world_spawn: Default world spawn position (x, y, z)
        """
        self.world_spawn = world_spawn
        self.safe_zones: List[Tuple[float, float, float]] = []
        
        # Spawn configuration
        self.min_player_distance = 10.0  # Don't spawn too close (reduced for smaller area)
        self.max_player_distance = 20.0  # Don't spawn too far (reduced for smaller area)
        self.spawn_radius = 16.0  # Match generated chunk area (3x3 chunks = -16 to +16)
        self.min_spawn_radius = 0.0  # Allow spawning at origin
        self.height_buffer = 5.0  # Height above terrain
        self.min_absolute_height = 5.0  # Minimum spawn height

        
    def add_safe_zone(self, position: Tuple[float, float, float]):
        """Register a designated safe spawn zone.
        
        Args:
            position: (x, y, z) coordinates of safe zone center
        """
        self.safe_zones.append(position)
    
    def find_spawn_position(
        self,
        terrain_system,
        existing_players: Optional[List[LVector3f]] = None,
        biome_registry = None
    ) -> Tuple[float, float, float]:
        """Find optimal spawn position using multi-tier fallback system.
        
        Args:
            terrain_system: TerrainSystem instance for height queries
            existing_players: List of existing player positions (LVector3f)
            biome_registry: BiomeRegistry class for biome queries
            
        Returns:
            Spawn position as (x, y, z) tuple
        """
        # Tier 1: Try spawning near existing players (cooperative)
        if existing_players and len(existing_players) > 0:
            spawn_pos = self._try_spawn_near_players(
                existing_players, terrain_system, biome_registry
            )
            if spawn_pos:
                print(f"✓ Spawning near players: {spawn_pos}")
                return spawn_pos
        
        # Tier 2: Try spawning in safe biome
        if biome_registry and terrain_system:
            spawn_pos = self._try_spawn_safe_biome(
                terrain_system, biome_registry
            )
            if spawn_pos:
                print(f"✓ Spawning in safe biome: {spawn_pos}")
                return spawn_pos

        
        # Tier 3: Try designated safe zones
        if self.safe_zones:
            spawn_pos = self._try_spawn_safe_zone(terrain_system)
            if spawn_pos:
                print(f"✓ Spawning in safe zone: {spawn_pos}")
                return spawn_pos
        
        # Tier 4: Fallback to world spawn
        print(f"⚠ Using world spawn fallback: {self.world_spawn}")
        return self.world_spawn
    
    def _try_spawn_near_players(
        self,
        players: List[LVector3f],
        terrain_system,
        biome_registry
    ) -> Optional[Tuple[float, float, float]]:
        """Attempt to spawn near existing players.
        
        Args:
            players: List of player positions
            terrain_system: For height queries
            biome_registry: For biome safety checks
            
        Returns:
            Spawn position or None if no valid location found
        """
        # Calculate average player position (team center)
        avg_x = sum(p.x for p in players) / len(players)
        avg_y = sum(p.y for p in players) / len(players)  # Panda3D Y is depth
        
        # Try multiple random positions in annulus around team
        for attempt in range(10):
            # Random angle
            angle = random.uniform(0, 2 * math.pi)
            
            # Random distance within min/max range
            distance = random.uniform(
                self.min_player_distance,
                self.max_player_distance
            )
            
            # Calculate position
            spawn_x = avg_x + distance * math.cos(angle)
            spawn_z = avg_y + distance * math.sin(angle)
            
            # Validate this position
            if self._is_valid_spawn(
                spawn_x, spawn_z, terrain_system, biome_registry
            ):
                # Get terrain height
                terrain_height = terrain_system.get_height(spawn_x, spawn_z)
                spawn_height = max(
                    self.min_absolute_height,
                    terrain_height + self.height_buffer
                )
                
                return (spawn_x, spawn_z, spawn_height)
        
        return None
    
    def _try_spawn_safe_biome(
        self,
        terrain_system,
        biome_registry
    ) -> Optional[Tuple[float, float, float]]:
        """Attempt to spawn in a safe biome.
        
        Args:
            terrain_system: For height queries
            biome_registry: For biome identification
            
        Returns:
            Spawn position or None if no valid location found
        """
        # Try random positions within spawn radius
        for attempt in range(20):
            # Random position in spawn radius
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(
                self.min_spawn_radius,
                self.spawn_radius
            )
            
            spawn_x = distance * math.cos(angle)
            spawn_z = distance * math.sin(angle)
            
            # Check if biome is safe
            biome = biome_registry.get_biome_at(spawn_x, spawn_z)
            if biome.name in self.SAFE_BIOMES:
                terrain_height = terrain_system.get_height(spawn_x, spawn_z)
                spawn_height = max(
                    self.min_absolute_height,
                    terrain_height + self.height_buffer
                )
                
                return (spawn_x, spawn_z, spawn_height)
        
        return None
    
    def _try_spawn_safe_zone(
        self,
        terrain_system
    ) -> Optional[Tuple[float, float, float]]:
        """Attempt to spawn in a designated safe zone.
        
        Args:
            terrain_system: For height queries
            
        Returns:
            Spawn position or None if no safe zones exist
        """
        if not self.safe_zones:
            return None
        
        # Pick random safe zone
        zone_x, zone_y, zone_z = random.choice(self.safe_zones)
        
        # Add small random offset
        offset_x = random.uniform(-5, 5)
        offset_z = random.uniform(-5, 5)
        
        spawn_x = zone_x + offset_x
        spawn_z = zone_y + offset_z  # Note: zone_y maps to spawn_z in Panda3D
        
        # Get accurate height
        terrain_height = terrain_system.get_height(spawn_x, spawn_z)
        spawn_height = max(
            self.min_absolute_height,
            terrain_height + self.height_buffer
        )
        
        return (spawn_x, spawn_z, spawn_height)
    
    def _is_valid_spawn(
        self,
        x: float,
        z: float,
        terrain_system,
        biome_registry
    ) -> bool:
        """Check if a position is valid for spawning.
        
        Args:
            x: World X coordinate
            z: World Z coordinate (Panda3D depth)
            terrain_system: For terrain queries
            biome_registry: For biome checks
            
        Returns:
            True if position is valid for spawning
        """
        # Check biome safety
        if biome_registry:
            biome = biome_registry.get_biome_at(x, z)
            if biome.name not in self.SAFE_BIOMES:
                return False
        
        # Check terrain height (avoid extreme heights)
        terrain_height = terrain_system.get_height(x, z)
        if terrain_height < -10 or terrain_height > 20:
            return False
        
        # Could add more checks here:
        # - Flatness (avoid steep slopes)
        # - Water depth
        # - Structure proximity
        
        return True


class SpawnProtection:
    """Manages temporary spawn protection for players."""
    
    def __init__(self, duration: float = 3.0):
        """Initialize spawn protection manager.
        
        Args:
            duration: Protection duration in seconds
        """
        self.duration = duration
        self.protected_players = {}  # player_id -> remaining_time
    
    def add_protection(self, player_id: str):
        """Grant spawn protection to a player.
        
        Args:
            player_id: Entity ID of player
        """
        self.protected_players[player_id] = self.duration
        print(f"🛡️ Spawn protection granted to {player_id} ({self.duration}s)")
    
    def update(self, dt: float):
        """Update protection timers.
        
        Args:
            dt: Delta time since last update
        """
        # Update timers
        expired = []
        for player_id, remaining in self.protected_players.items():
            remaining -= dt
            if remaining <= 0:
                expired.append(player_id)
            else:
                self.protected_players[player_id] = remaining
        
        # Remove expired protections
        for player_id in expired:
            del self.protected_players[player_id]
            print(f"🛡️ Spawn protection expired for {player_id}")
    
    def is_protected(self, player_id: str) -> bool:
        """Check if a player has spawn protection.
        
        Args:
            player_id: Entity ID of player
            
        Returns:
            True if player is currently protected
        """
        return player_id in self.protected_players
    
    def remove_protection(self, player_id: str):
        """Manually remove spawn protection (e.g., player attacked).
        
        Args:
            player_id: Entity ID of player
        """
        if player_id in self.protected_players:
            del self.protected_players[player_id]
            print(f"🛡️ Spawn protection removed from {player_id} (attacked)")
