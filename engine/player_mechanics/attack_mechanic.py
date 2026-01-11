"""Attack mechanic for player control system."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.input.keybindings import InputAction


class AttackMechanic(PlayerMechanic):
    """Handles attack input and publishes attack events.
    
    This mechanic detects attack input (Mouse1) and publishes
    an attack_input event for the CombatSystem to handle.
    """
    
    priority = 53  # Run after parry (54), before camera (10)
    exclusive = False
    
    def initialize(self, player_id: int, world):
        """Called when player is ready."""
        super().initialize(player_id, world)
        self.hitbox_active = False
        self.hit_entities = set()
        self.current_multiplier = 1.0
        
        # Subscribe to combat events
        world.event_bus.subscribe("combat_hit_start", self._on_hit_start)
        world.event_bus.subscribe("combat_hit_end", self._on_hit_end)
        
    def _on_hit_start(self, data):
        """Enable hitbox for damage dealing."""
        if data.entity_id == self._player_id:
            self.hitbox_active = True
            self.hit_entities.clear()
            self.current_multiplier = getattr(data, 'damage_multiplier', 1.0)
            # print(f"⚔️ AttackMechanic: Hitbox ACTIVE (mult={self.current_multiplier})")
            
    def _on_hit_end(self, data):
        """Disable hitbox."""
        if data.entity_id == self._player_id:
            self.hitbox_active = False
            # print("⚔️ AttackMechanic: Hitbox END")
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        """Always enabled."""
        return True
    
    def update(self, ctx: PlayerContext) -> None:
        """Check for attack input and handle active hitbox.
        
        Args:
            ctx: Player context with input state
        """
        # 1. Input Processing
        attack_pressed = ctx.input.is_action_active(InputAction.ATTACK_PRIMARY)
        
        # Detect rising edge (just pressed)
        if attack_pressed and not getattr(self, 'attack_pressed_last_frame', False):
            # Publish attack input event
            ctx.world.event_bus.publish("attack_input", entity_id=ctx.player_id)
        
        self.attack_pressed_last_frame = attack_pressed
        
        # Update particles if they exist
        if hasattr(self, 'particle_system'):
            self.particle_system.update(ctx.dt)
        
        # 2. Hitbox Logic (if active)
        if self.hitbox_active:
            self._process_hitbox(ctx)
            
    def _process_hitbox(self, ctx: PlayerContext):
        """Check for entities within attack cone."""
        from engine.components.core import Health, Transform
        from panda3d.core import LVector3f
        from engine.animation.particles import VoxelParticleSystem, create_impact_effect
        
        render = ctx.world.base.render
        player_pos = ctx.transform.position
        
        # Initialize particle system on demand if needed
        if not hasattr(self, 'particle_system'):
            self.particle_system = VoxelParticleSystem(ctx.world.base.render, max_particles=100)
        # Calculate forward vector from camera orientation (since avatar follows camera or movement)
        from engine.components.camera_state import CameraState
        camera_state = ctx.world.get_component(ctx.player_id, CameraState)
        if camera_state:
            import math
            h_rad = math.radians(camera_state.yaw)
            player_fwd = LVector3f(-math.sin(h_rad), math.cos(h_rad), 0)
        else:
            player_fwd = LVector3f(0, 1, 0)
        player_fwd.normalize()
        
        # Attack range and angle
        attack_range = 2.5
        attack_angle_cos = 0.5  # ~60 degrees (cos(60)=0.5)
        
        # Iterate over potential targets with Health
        # Ideally use spatial partition, but for now iterate all Health entities
        for target_id in ctx.world.get_entities_with(Health):
            if target_id == ctx.player_id:
                continue
                
            if target_id in self.hit_entities:
                continue
                
            target_transform = ctx.world.get_component(target_id, Transform)
            if not target_transform:
                continue
            
            # Distance check
            to_target = target_transform.position - player_pos
            dist_sq = to_target.lengthSquared()
            
            if dist_sq > attack_range * attack_range:
                continue
                
            # Angle check (dot product)
            to_target.normalize()
            dot = player_fwd.dot(to_target)
            
            if dot > attack_angle_cos:
                # Valid hit!
                self.hit_entities.add(target_id)
                
                # Apply damage
                damage = 10.0 * self.current_multiplier
                ctx.world.event_bus.publish("on_entity_damage", 
                    entity_id=target_id, 
                    amount=damage,
                    source=ctx.player_id
                )
                
                # Visual feedback event
                ctx.world.event_bus.publish("combat_hit_confirm",
                    target_id=target_id,
                    position=target_transform.position
                )
                
                # Emit particles
                if hasattr(self, 'particle_system'):
                    # Calculate hit normal (direction from target to player, roughly)
                    hit_normal = (player_pos - target_transform.position).normalized()
                    create_impact_effect(
                        self.particle_system,
                        target_transform.position + LVector3f(0, 0, 1.0), # Hit "center" roughly
                        hit_normal
                    )
                    self.particle_system.update(0.01) # Force immediate update? No, needs loop.

                print(f"💥 HIT entity {target_id} for {damage} damage!")
