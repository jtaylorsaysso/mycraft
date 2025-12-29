"""Dodge system with timing-based stamina costs and i-frames."""

from engine.ecs.system import System
from engine.components.core import Stamina, Health, CombatState
from engine.input.keybindings import InputAction
from typing import Dict


class DodgeSystem(System):
    """Handles dodge rolls with timing-based stamina costs and invulnerability frames.
    
    Dodge provides:
    - Directional roll movement
    - I-frames (invulnerability) during dodge
    - Stamina cost that scales with timing quality
    """
    
    # Dodge timing windows (seconds before incoming hit)
    PERFECT_WINDOW = 0.05  # Center timing
    GOOD_WINDOW = 0.15     # Acceptable timing
    MAX_WINDOW = 0.2       # Outside this = failed dodge
    
    # Stamina costs
    PERFECT_COST = 15
    GOOD_COST = 25
    FAILED_COST = 35
    
    # I-frame duration
    IFRAME_DURATION = 0.3  # seconds of invulnerability
    
    # Dodge movement
    DODGE_DISTANCE = 2.5  # units
    DODGE_DURATION = 0.4  # seconds
    
    def initialize(self):
        """Initialize dodge system and subscribe to input events."""
        self.event_bus.subscribe("dodge_input", self.on_dodge_input)
        self.active_dodges: Dict[str, float] = {}  # entity_id -> dodge_end_time
    
    def update(self, dt: float):
        """Update active dodges and clear expired i-frames.
        
        Args:
            dt: Delta time in seconds
        """
        # Accumulate time
        if not hasattr(self, '_accumulated_time'):
            self._accumulated_time = 0.0
        self._accumulated_time += dt
        
        # Clear expired dodges and reset state
        expired = [eid for eid, end_time in self.active_dodges.items() 
                   if self._accumulated_time > end_time]
        for eid in expired:
            del self.active_dodges[eid]
            health = self.world.get_component(eid, Health)
            if health:
                health.invulnerable = False
            
            # Reset combat state to idle
            combat_state = self.world.get_component(eid, CombatState)
            if combat_state:
                combat_state.state = "idle"
                combat_state.state_timer = 0.0
                combat_state.can_attack = True
                combat_state.can_dodge = True
                combat_state.can_parry = True
                print("✅ Ready for action")
    
    def on_dodge_input(self, event):
        """Handle dodge input event.
        
        Args:
            event: Event with entity_id field
        """
        entity_id = event.entity_id
        
        # Check combat state
        combat_state = self.world.get_component(entity_id, CombatState)
        if not combat_state:
            return
        
        # Check if can dodge
        if not combat_state.can_dodge:
            print("⚠️ Cannot dodge right now")
            return
        
        # Check stamina availability
        stamina = self.world.get_component(entity_id, Stamina)
        if not stamina or stamina.current < self.PERFECT_COST:
            return  # Not enough stamina for even perfect dodge
        
        # Calculate timing quality (for now, always perfect - TODO: check incoming attacks)
        timing_quality = self._calculate_timing_quality(entity_id)
        stamina_cost = self._get_stamina_cost(timing_quality)
        
        if stamina.current < stamina_cost:
            return  # Not enough stamina for this timing
        
        # Consume stamina
        stamina.current -= stamina_cost
        stamina.regen_timer = stamina.regen_delay
        
        # Update combat state
        combat_state.state = "dodging"
        combat_state.state_timer = 0.0
        combat_state.can_attack = False
        combat_state.can_dodge = False
        combat_state.can_parry = False
        
        print("🏃 DODGING")
        
        # Apply i-frames
        health = self.world.get_component(entity_id, Health)
        if health:
            health.invulnerable = True
            # Initialize time if needed
            if not hasattr(self, '_accumulated_time'):
                self._accumulated_time = 0.0
            self.active_dodges[entity_id] = self._accumulated_time + self.IFRAME_DURATION
        
        # Apply dodge movement
        self._apply_dodge_movement(entity_id)
        
        # Publish dodge executed event
        self.event_bus.publish("dodge_executed", 
                              entity_id=entity_id,
                              timing_quality=timing_quality)
    
    def _calculate_timing_quality(self, entity_id: str) -> str:
        """Calculate timing quality based on incoming attacks.
        
        TODO: Implement actual timing detection based on enemy attack windups.
        For now, returns "perfect" as placeholder.
        
        Args:
            entity_id: Entity performing dodge
            
        Returns:
            Timing quality: "perfect", "good", or "failed"
        """
        # Placeholder - always perfect for MVP
        return "perfect"
    
    def _get_stamina_cost(self, quality: str) -> float:
        """Get stamina cost for timing quality.
        
        Args:
            quality: Timing quality string
            
        Returns:
            Stamina cost
        """
        return {
            "perfect": self.PERFECT_COST,
            "good": self.GOOD_COST,
            "failed": self.FAILED_COST
        }.get(quality, self.FAILED_COST)
    
    def _apply_dodge_movement(self, entity_id: str):
        """Apply directional dodge roll movement using direct position impulse.
        
        Instead of setting velocity (which gets overridden), we apply
        a direct position offset in the dodge direction.
        
        Args:
            entity_id: Entity performing dodge
        """
        from engine.components.core import CombatState, Transform
        from panda3d.core import LVector3f
        
        # Get combat state for dodge direction
        combat_state = self.world.get_component(entity_id, CombatState)
        if not combat_state:
            return
        
        # Get dodge direction (set by AnimationMechanic)
        direction = combat_state.dodge_direction
        
        # Get transform for position application
        transform = self.world.get_component(entity_id, Transform)
        if not transform:
            return
        
        # Apply immediate position offset (dodge distance in direction)
        # This gives instant movement that won't be overridden by movement system
        dodge_offset = direction * self.DODGE_DISTANCE
        transform.position += dodge_offset
        
        print(f"🏃 Dodge: moved {self.DODGE_DISTANCE} units in direction {direction}")
        
        # Publish dodge movement event for animation system
        self.event_bus.publish("dodge_movement_applied",
                              entity_id=entity_id,
                              direction=direction,
                              distance=self.DODGE_DISTANCE)
