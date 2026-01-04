"""Swimming mechanic for player control in water."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from panda3d.core import LVector3f


class SwimmingMechanic(PlayerMechanic):
    """Handles swimming controls when player is in water."""
    
    priority = 40  # Higher priority than ground movement (50)
    exclusive = False  # Allow other mechanics to run (Camera, Dodge, etc.)
    
    # Swimming physics constants
    SWIM_UP_FORCE = 12.0  # Upward acceleration when swimming up
    SWIM_DOWN_FORCE = 8.0  # Downward acceleration when swimming down
    WATER_SPEED_MULT = 0.6  # Horizontal speed reduced to 60% in water
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        """Only handle when player is in water."""
        return hasattr(ctx.state, 'in_water') and ctx.state.in_water
    
    def update(self, ctx: PlayerContext) -> None:
        """Apply swimming controls."""
        # Vertical swimming controls
        if ctx.input.jump:
            # Swim up
            ctx.state.velocity_z += self.SWIM_UP_FORCE * ctx.dt
        
        if ctx.input.crouch:
            # Swim down
            ctx.state.velocity_z -= self.SWIM_DOWN_FORCE * ctx.dt
        
        # Horizontal movement speed reduction in water
        # (applied after ground_movement calculates base movement)
        # This reduces horizontal velocity when in water
        if ctx.state.submersion_level > 0.5:
            # Fully submerged: strong water resistance
            ctx.state.velocity_x *= self.WATER_SPEED_MULT
            ctx.state.velocity_y *= self.WATER_SPEED_MULT
        elif ctx.state.submersion_level > 0.0:
            # Partially submerged: less resistance
            mult = 0.8  # 80% speed
            ctx.state.velocity_x *= mult
            ctx.state.velocity_y *= mult
