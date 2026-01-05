"""
Enemy System.

Handles enemy AI behavior and visual representation management.
"""

from engine.ecs.system import System
from engine.components.core import Transform, Health, CombatState
from engine.components.enemy import EnemyComponent
from engine.physics import KinematicState
from engine.rendering.enemy_visual import EnemyVisual
from engine.core.logger import get_logger
from panda3d.core import LVector3f

import random

logger = get_logger(__name__)

class EnemySystem(System):
    """
    Manages enemies:
    1. AI Logic (State Machine)
    2. Visual Representation (VoxelAvatar)
    """
    
    def __init__(self, world, event_bus, game):
        super().__init__(world, event_bus)
        self.game = game
        self.visuals = {}  # entity_id -> EnemyVisual
        
        # Subscribe to death to clean up visuals
        self.event_bus.subscribe("entity_death", self.on_entity_death)
        
    def on_entity_death(self, event):
        """Clean up visual when enemy dies."""
        entity_id = event.entity_id
        if entity_id in self.visuals:
            self.visuals[entity_id].destroy()
            del self.visuals[entity_id]
            
    def update(self, dt: float):
        """Update AI and Visuals."""
        
        # 1. Get player position for AI
        player_pos = None
        player_id = self.world.get_entity_by_tag("player")
        if player_id:
            pt = self.world.get_component(player_id, Transform)
            if pt:
                player_pos = pt.position
        
        # 2. Process all enemies
        enemies = self.world.get_entities_with(EnemyComponent, Transform, Health)
        
        for entity_id in enemies:
            enemy = self.world.get_component(entity_id, EnemyComponent)
            transform = self.world.get_component(entity_id, Transform)
            health = self.world.get_component(entity_id, Health)
            kinematic = self.world.get_component(entity_id, KinematicState) # Optional?
            combat = self.world.get_component(entity_id, CombatState)
            
            # --- Visual Management ---
            if entity_id not in self.visuals:
                # Create visual
                self._create_visual(entity_id, enemy, transform)
            
            # Sync visual transform
            if entity_id in self.visuals:
                visual = self.visuals[entity_id]
                visual.root.setPos(transform.position)
                # Sync rotation? For now, look at target or just simple rotation
                if enemy.ai_state != "idle" and player_pos:
                    visual.root.lookAt(player_pos)
                    # Constrain pitch needed? VoxelAvatar might handle it
            
            # --- AI Logic ---
            if not player_pos or health.current <= 0:
                continue
                
            dist_sq = (transform.position - player_pos).length_squared()
            
            self._update_ai(dt, entity_id, enemy, transform, player_pos, dist_sq, combat)
            
    def _create_visual(self, entity_id, enemy_comp, transform):
        """Instantiate EnemyVisual."""
        # Attach to render via Game instance or similar
        # We need a parent node. Usually 'render' or a specialized node
        parent = self.game.render
        
        # Create anchor node for this enemy
        node = parent.attachNewNode(f"enemy_{entity_id}")
        node.setPos(transform.position)
        
        visual = EnemyVisual(node, enemy_comp.enemy_type, enemy_comp.tint_color)
        self.visuals[entity_id] = visual
        logger.debug(f"Created visual for enemy {entity_id} ({enemy_comp.enemy_type})")
        
    def _update_ai(self, dt, entity_id, enemy, transform, player_pos, dist_sq, combat):
        """Simple State Machine."""
        
        # State transitions
        if enemy.ai_state == "idle":
            # Check aggro
            if dist_sq < enemy.aggro_range * enemy.aggro_range:
                enemy.ai_state = "aggro"
                logger.debug(f"Enemy {entity_id} aggroed!")
                
        elif enemy.ai_state == "aggro":
            # Move towards player
            if dist_sq > enemy.aggro_range * enemy.aggro_range * 1.5:
                # De-aggro
                enemy.ai_state = "idle"
            elif dist_sq < enemy.attack_range * enemy.attack_range:
                # Start attack
                enemy.ai_state = "windup"
                enemy.state_timer = 1.5 if enemy.enemy_type == "skeleton" else 2.0
            else:
                # Move
                direction = (player_pos - transform.position)
                direction.z = 0 # planar movement
                direction.normalize()
                
                speed = 4.0 if enemy.enemy_type == "skeleton" else 2.0
                
                # Apply velocity via KinematicState if available, else manual
                # Ideally use Physics system. For now, manual/transform update
                # But Collision system handles physics.
                # So we should set velocity on KinematicState
                kinematic = self.world.get_component(entity_id, KinematicState)
                if kinematic:
                    # Update velocity in component; PhysicsSystem will move it
                    # Note: PhysicsSystem runs separately.
                    from engine.physics.kinematic import KinematicState
                    # We can't edit component in place if it's a dataclass frozen? No they aren't frozen
                    kinematic.velocity_x = direction.x * speed
                    kinematic.velocity_z = direction.y * speed # Z is Y in panda logic for 2D velocity?
                                                        # Pandas Z is Up. Input usually X/Y.
                                                        # KinematicState uses x, y, z.
                    kinematic.velocity_y = direction.y * speed
                    
                    # Update transform to face movement
                    # handled by lookAt above
                
        elif enemy.ai_state == "windup":
            # Stop moving
            kinematic = self.world.get_component(entity_id, KinematicState)
            if kinematic:
                kinematic.velocity_x = 0
                kinematic.velocity_y = 0
                
            enemy.state_timer -= dt
            if enemy.state_timer <= 0:
                enemy.ai_state = "attack"
                
        elif enemy.ai_state == "attack":
            # Execute attack
            # Use CombatSystem input event
            from games.voxel_world.systems.combat_system import MockEvent # Or proper event
            # Actually, CombatSystem listens for `on_attack_input`
            # We can publish it OR call method if we have access
            
            # Using EventBus
            self.event_bus.publish("on_attack_input", entity_id=entity_id)
            
            enemy.ai_state = "recovery"
            enemy.state_timer = 1.0
            
        elif enemy.ai_state == "recovery":
            enemy.state_timer -= dt
            if enemy.state_timer <= 0:
                enemy.ai_state = "aggro"
