"""Parry system with timing-based damage mitigation."""

from engine.ecs.system import System
from engine.components.core import Stamina, Health, CombatState
from engine.input.keybindings import InputAction
from typing import Dict, Tuple


class ParrySystem(System):
    """Handles parry with timing-based damage mitigation.
    
    Parry provides:
    - Damage mitigation without movement (stand your ground)
    - Lower stamina cost than dodge
    - Timing-based mitigation percentage
    """
    
    # Parry timing windows (seconds before incoming hit)
    PERFECT_WINDOW = 0.03  # Center timing
    GOOD_WINDOW = 0.12     # Acceptable timing
    MAX_WINDOW = 0.15      # Outside this = failed parry
    
    # Stamina costs
    PERFECT_COST = 5
    GOOD_COST = 15
    FAILED_COST = 20
    
    # Damage mitigation percentages
    PERFECT_MITIGATION = 1.0   # 100% block
    GOOD_MITIGATION = 0.7      # 70% block
    FAILED_MITIGATION = 0.3    # 30% block
    
    def initialize(self):
        """Initialize parry system and subscribe to events."""
        self.event_bus.subscribe("parry_input", self.on_parry_input)
        # Intercept damage events BEFORE DamageSystem processes them
        # Note: Subscription order matters - ParrySystem should be registered
        # before DamageSystem to intercept damage first
        self.event_bus.subscribe("on_entity_damage", self.on_damage_before_system)
        
        # Track active parries: entity_id -> (end_time, mitigation_percent)
        self.active_parries: Dict[str, Tuple[float, float]] = {}
    
    def update(self, dt: float):
        """Update active parries and clear expired ones.
        
        Args:
            dt: Delta time in seconds
        """
        # Accumulate time
        if not hasattr(self, '_accumulated_time'):
            self._accumulated_time = 0.0
        self._accumulated_time += dt
        
        # Clear expired parries and reset state
        expired = [eid for eid, (end_time, _) in self.active_parries.items() 
                   if self._accumulated_time > end_time]
        for eid in expired:
            del self.active_parries[eid]
            
            # Reset combat state to idle
            combat_state = self.world.get_component(eid, CombatState)
            if combat_state:
                combat_state.state = "idle"
                combat_state.state_timer = 0.0
                combat_state.can_attack = True
                combat_state.can_dodge = True
                combat_state.can_parry = True
                print("✅ Ready for action")
    
    def on_parry_input(self, event):
        """Handle parry input event.
        
        Args:
            event: Event with entity_id field
        """
        entity_id = event.entity_id
        
        # Check combat state
        combat_state = self.world.get_component(entity_id, CombatState)
        if not combat_state:
            return
        
        # Check if can parry
        if not combat_state.can_parry:
            print("⚠️ Cannot parry right now")
            return
        
        # Check stamina availability
        stamina = self.world.get_component(entity_id, Stamina)
        if not stamina or stamina.current < self.PERFECT_COST:
            return  # Not enough stamina for even perfect parry
        
        # Calculate timing quality (placeholder - always perfect for MVP)
        timing_quality = self._calculate_timing_quality(entity_id)
        stamina_cost = self._get_stamina_cost(timing_quality)
        
        if stamina.current < stamina_cost:
            return  # Not enough stamina for this timing
        
        # Consume stamina
        stamina.current -= stamina_cost
        stamina.regen_timer = stamina.regen_delay
        
        # Update combat state
        combat_state.state = "parrying"
        combat_state.state_timer = 0.0
        combat_state.can_attack = False
        combat_state.can_dodge = False
        combat_state.can_parry = False
        
        print("🛡️ PARRYING")
        
        # Activate parry window
        mitigation = self._get_mitigation(timing_quality)
        # Initialize time if needed
        if not hasattr(self, '_accumulated_time'):
            self._accumulated_time = 0.0
        self.active_parries[entity_id] = (
            self._accumulated_time + self.MAX_WINDOW,
            mitigation
        )
        
        # Publish parry executed event
        self.event_bus.publish("parry_executed", 
                              entity_id=entity_id,
                              timing_quality=timing_quality,
                              mitigation=mitigation)
    
    def on_damage_before_system(self, event):
        """Intercept damage events to apply parry mitigation.
        
        This runs BEFORE DamageSystem processes the damage.
        
        Args:
            event: Damage event with target_id and damage fields
        """
        target_id = event.target_id
        
        # Check if target has active parry
        if target_id in self.active_parries:
            _, mitigation = self.active_parries[target_id]
            
            # Apply mitigation to damage
            original_damage = event.damage
            event.damage = original_damage * (1.0 - mitigation)
            
            # Consume parry (one-time use)
            del self.active_parries[target_id]
            
            # Publish parry success event
            self.event_bus.publish("parry_success",
                                  entity_id=target_id,
                                  original_damage=original_damage,
                                  mitigated_damage=event.damage,
                                  mitigation_percent=mitigation)
    
    def _calculate_timing_quality(self, entity_id: str) -> str:
        """Calculate timing quality based on incoming attacks.
        
        TODO: Implement actual timing detection based on enemy attack windups.
        For now, returns "perfect" as placeholder.
        
        Args:
            entity_id: Entity performing parry
            
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
    
    def _get_mitigation(self, quality: str) -> float:
        """Get damage mitigation percentage for timing quality.
        
        Args:
            quality: Timing quality string
            
        Returns:
            Mitigation percentage (0.0 to 1.0)
        """
        return {
            "perfect": self.PERFECT_MITIGATION,
            "good": self.GOOD_MITIGATION,
            "failed": self.FAILED_MITIGATION
        }.get(quality, 0.0)
    
    def _get_current_time(self) -> float:
        """Get current game time.
        
        Returns:
            Current time in seconds
        """
        # Use world's time if available, otherwise use a simple counter
        if hasattr(self.world, 'time'):
            return self.world.time
        # Fallback: accumulate from updates (less accurate)
        if not hasattr(self, '_accumulated_time'):
            self._accumulated_time = 0.0
        return self._accumulated_time
