from ursina import Ursina, Entity, color, Vec3, time

from engine.player import Player


class Slime(Entity):
    """Simple slime AI with patrol/aggro/chase states."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_slime = True
        self.hp = 3
        self.speed = 1.5
        self.aggro_range = 4.0
        self.state = 'patrol'
        self.patrol_waypoints = [(8, 0.5, 10), (8, 0.5, 14)]
        self.current_waypoint_index = 0
        self.target_waypoint = self.patrol_waypoints[0]
        self.patrol_direction = 1  # 1 for forward, -1 for reverse

    def update_ai(self, player):
        """Update AI state and movement each frame."""
        if getattr(self, 'is_dead', False):
            return

        dist_to_player = (self.world_position - player.world_position).length()

        # State transitions
        if self.state == 'patrol' and dist_to_player <= self.aggro_range:
            self.state = 'aggro'
        elif self.state == 'aggro':
            self.state = 'chase'
        elif self.state == 'chase' and dist_to_player > self.aggro_range * 1.5:
            self.state = 'patrol'
            # Reset patrol to nearest waypoint
            self._reset_patrol()

        # Movement logic
        if self.state == 'patrol':
            self._patrol()
        elif self.state == 'chase':
            self._chase(player)

    def _patrol(self):
        """Move back and forth between waypoints."""
        target = Vec3(*self.target_waypoint)
        direction = (target - self.world_position).normalized()
        self.position += direction * self.speed * time.dt

        # Check if reached waypoint (within threshold)
        if (self.world_position - target).length() < 0.2:
            # Switch to next waypoint
            self.current_waypoint_index += self.patrol_direction
            if self.current_waypoint_index >= len(self.patrol_waypoints):
                self.current_waypoint_index = len(self.patrol_waypoints) - 2
                self.patrol_direction = -1
            elif self.current_waypoint_index < 0:
                self.current_waypoint_index = 1
                self.patrol_direction = 1
            self.target_waypoint = self.patrol_waypoints[self.current_waypoint_index]

    def _chase(self, player):
        """Move toward the player."""
        direction = (player.world_position - self.world_position).normalized()
        self.position += direction * self.speed * time.dt

    def _reset_patrol(self):
        """Reset patrol to the nearest waypoint."""
        min_dist = float('inf')
        nearest_idx = 0
        for i, wp in enumerate(self.patrol_waypoints):
            d = (self.world_position - Vec3(*wp)).length()
            if d < min_dist:
                min_dist = d
                nearest_idx = i
        self.current_waypoint_index = nearest_idx
        self.target_waypoint = self.patrol_waypoints[nearest_idx]
        self.patrol_direction = 1


def setup_room1_arena():
    """Create a simple 16x16 arena with walls and a single slime dummy."""
    # Floor: single large cube so top is at y=0
    floor = Entity(
        model='cube',
        color=color.gray,
        scale=(16, 1, 16),
        position=(8, -0.5, 8),  # so top surface is y=0
        collider='box',
    )

    wall_height = 3
    half = 8

    # North wall (z = 0)
    Entity(
        model='cube',
        color=color.rgb(80, 80, 80),
        scale=(16, wall_height, 1),
        position=(half, wall_height / 2, 0),
        collider='box',
    )

    # South wall (z = 16)
    Entity(
        model='cube',
        color=color.rgb(80, 80, 80),
        scale=(16, wall_height, 1),
        position=(half, wall_height / 2, 16),
        collider='box',
    )

    # West wall (x = 0)
    Entity(
        model='cube',
        color=color.rgb(60, 60, 60),
        scale=(1, wall_height, 16),
        position=(0, wall_height / 2, half),
        collider='box',
    )

    # East wall (x = 16)
    Entity(
        model='cube',
        color=color.rgb(60, 60, 60),
        scale=(1, wall_height, 16),
        position=(16, wall_height / 2, half),
        collider='box',
    )

    # Slime with AI
    slime = Slime(
        model='cube',
        color=color.lime,
        scale=(1, 1, 1),
        position=(8, 0.5, 12),
        collider='box',
    )

    # Player spawn roughly centered toward south side of room
    player = Player(start_pos=(8, 2, 4), networking=False)

    return player, slime


def run_room1_demo():
    """Run the Room 1 combat sandbox demo as a standalone entrypoint."""
    app = Ursina()
    player, slime = setup_room1_arena()

    # Update slime AI each frame (avoid dynamic update assignment)
    def update():
        slime.update_ai(player)

    app.update = update
    app.run()
