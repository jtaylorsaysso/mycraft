"""Combat system with attack execution, hit detection, and momentum damage."""

from engine.ecs.system import System
from engine.components.core import Transform, Health, CombatState
from engine.physics import KinematicState
from engine.input.keybindings import InputAction
from panda3d.core import LVector3f
from typing import Dict, Set
import math


class CombatSystem(System):
    """Handles attack execution, hit detection, and damage calculation.
    
    Features:
    - Primary attack with timing windows
    - Momentum-based damage formula
    - Sphere-based hit detection
    - One hit per attack limit
    """
    
    # Attack timing
    ATTACK_DURATION = 0.5  # Total animation time
    HIT_WINDOW_START = 0.12  # When damage can be dealt
    HIT_WINDOW_END = 0.18  # When damage window closes
    CANCEL_WINDOW = 0.35  # When player can cancel into other actions
    
    # Damage
    BASE_DAMAGE = 25.0
    HIT_RANGE = 2.0  # Units from player
    
    def initialize(self):
        """Initialize combat system and subscribe to input events."""
        self.event_bus.subscribe("attack_input", self.on_attack_input)
        
        # Track active attacks: entity_id -> attack_state
        self.active_attacks: Dict[str, 'AttackState'] = {}
    
    def update(self, dt: float):
        """Update active attacks and process hit detection.
        
        Args:
            dt: Delta time in seconds
        """
        # Accumulate time
        if not hasattr(self, '_accumulated_time'):
            self._accumulated_time = 0.0
        self._accumulated_time += dt
        
        # Update all active attacks
        completed = []
        for entity_id, attack in list(self.active_attacks.items()):
            attack.elapsed_time += dt
            
            # Update combat state
            combat_state = self.world.get_component(entity_id, CombatState)
            if combat_state:
                combat_state.state_timer += dt
                
                # Enable cancel after cancel window
                if attack.elapsed_time >= self.CANCEL_WINDOW and not combat_state.can_cancel:
                    combat_state.can_cancel = True
                    combat_state.can_dodge = True
            
            # Check if in hit window and haven't hit yet
            if (attack.elapsed_time >= self.HIT_WINDOW_START and 
                attack.elapsed_time <= self.HIT_WINDOW_END and 
                not attack.has_hit):
                # Perform hit detection
                self._check_hit(entity_id, attack)
            
            # Check if attack completed
            if attack.elapsed_time >= self.ATTACK_DURATION:
                completed.append(entity_id)
        
        # Remove completed attacks and reset state
        for entity_id in completed:
            del self.active_attacks[entity_id]
            
            # Reset combat state to idle
            combat_state = self.world.get_component(entity_id, CombatState)
            if combat_state:
                combat_state.state = "idle"
                combat_state.state_timer = 0.0
                combat_state.can_cancel = True
                combat_state.can_attack = True
                combat_state.can_dodge = True
                combat_state.can_parry = True
                print("✅ Ready for action")
    
    def on_attack_input(self, event):
        """Handle attack input event.
        
        Args:
            event: Event with entity_id field
        """
        entity_id = event.entity_id
        
        # Check combat state
        combat_state = self.world.get_component(entity_id, CombatState)
        if not combat_state:
            return
        
        # Check if can attack
        if not combat_state.can_attack:
            print("⚠️ Cannot attack right now")
            return
        
        # Check if already attacking
        if entity_id in self.active_attacks:
            return  # Can't attack while already attacking
        
        # Update combat state
        combat_state.state = "attacking"
        combat_state.state_timer = 0.0
        combat_state.can_attack = False
        combat_state.can_dodge = False  # Locked until cancel window
        combat_state.can_parry = False
        
        print("⚔️ ATTACKING")
        
        # Start new attack
        self.active_attacks[entity_id] = AttackState()
        
        # Publish attack started event
        self.event_bus.publish("attack_started", entity_id=entity_id)
    
    def _check_hit(self, attacker_id: str, attack: 'AttackState'):
        """Check for hits during attack window.
        
        Args:
            attacker_id: Entity performing attack
            attack: Attack state object
        """
        # Get attacker position
        attacker_transform = self.world.get_component(attacker_id, Transform)
        if not attacker_transform:
            return
        
        attacker_pos = attacker_transform.position
        
        # Get attacker velocity for momentum damage
        attacker_state = self.world.get_component(attacker_id, KinematicState)
        velocity_magnitude = 0.0
        if attacker_state:
            velocity = LVector3f(
                attacker_state.velocity_x,
                attacker_state.velocity_y,
                attacker_state.velocity_z
            )
            velocity_magnitude = velocity.length()
        
        # Find entities in range
        hit_entities = self._find_entities_in_range(attacker_id, attacker_pos, self.HIT_RANGE)
        
        # Apply damage to first valid target
        for target_id in hit_entities:
            # Check if target has health
            target_health = self.world.get_component(target_id, Health)
            if not target_health:
                continue
            
            # Calculate damage with momentum bonus
            damage = self._calculate_damage(self.BASE_DAMAGE, velocity_magnitude)
            
            # Publish damage event (ParrySystem may intercept)
            self.event_bus.publish("on_entity_damage",
                                  target_id=target_id,
                                  attacker_id=attacker_id,
                                  damage=damage)
            
            # Mark attack as having hit (one hit per attack)
            attack.has_hit = True
            
            # Publish hit event
            self.event_bus.publish("attack_hit",
                                  attacker_id=attacker_id,
                                  target_id=target_id,
                                  damage=damage)
            break  # Only hit one target per attack
    
    def _find_entities_in_range(self, attacker_id: str, attacker_pos: LVector3f, range: float) -> Set[str]:
        """Find all entities within attack range.
        
        Args:
            attacker_id: Entity performing attack (to exclude)
            attacker_pos: Position of attacker
            range: Attack range in units
            
        Returns:
            Set of entity IDs in range
        """
        entities_in_range = set()
        
        # Check all entities with Transform
        for entity_id in self.world.get_entities_with(Transform):
            # Skip self
            if entity_id == attacker_id:
                continue
            
            # Get entity position
            transform = self.world.get_component(entity_id, Transform)
            if not transform:
                continue
            
            # Calculate distance
            distance = (transform.position - attacker_pos).length()
            
            # Check if in range
            if distance <= range:
                entities_in_range.add(entity_id)
        
        return entities_in_range
    
    def _calculate_damage(self, base_damage: float, velocity_magnitude: float) -> float:
        """Calculate damage with momentum bonus.
        
        Formula: damage = base_damage + velocity_magnitude
        
        Args:
            base_damage: Base damage value
            velocity_magnitude: Attacker's velocity magnitude
            
        Returns:
            Final damage value
        """
        return base_damage + velocity_magnitude
    
    def _get_current_time(self) -> float:
        """Get current game time.
        
        Returns:
            Current time in seconds
        """
        if hasattr(self.world, 'time'):
            return self.world.time
        if not hasattr(self, '_accumulated_time'):
            self._accumulated_time = 0.0
        return self._accumulated_time


class AttackState:
    """Tracks state of an active attack."""
    
    def __init__(self):
        self.elapsed_time = 0.0
        self.has_hit = False
