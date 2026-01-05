"""
Loot System.

Handles spawning loot on death and picking up items.
Now with visual representation for pickups.
"""

from engine.ecs.system import System
from engine.components.core import Transform
from engine.components.loot import LootComponent, PickupComponent
from engine.components.avatar_colors import AvatarColors
from engine.color.palette import ColorPalette
from engine.rendering.pickup_visual import PickupVisual
from panda3d.core import LVector3f
from direct.showbase.ShowBase import ShowBase

class LootSystem(System):
    """Manages loot drops and pickups."""
    
    def __init__(self, world, event_bus):
        super().__init__(world, event_bus)
        self.visuals = {}  # entity_id -> PickupVisual
        self.base = None
        
    def initialize(self):
        self.event_bus.subscribe("entity_death", self.on_entity_death)
        
        # Try to find base for rendering
        try:
            self.base = ShowBase.Global.base
        except:
            self.base = None
        
    def on_entity_death(self, event):
        """Handle death event to spawn loot."""
        entity_id = event.entity_id
        position = event.position
        
        if not position:
            return
            
        loot = self.world.get_component(entity_id, LootComponent)
        if loot and loot.color_name:
            self.spawn_color_swatch(loot.color_name, position)
            
    def spawn_color_swatch(self, color_name: str, position: LVector3f):
        """Spawn a color swatch pickup."""
        entity = self.world.create_entity()
        
        # Add components
        # Convert position to LVector3f if it isn't already (event might pass tuple or Vec3)
        pos_vec = LVector3f(position[0], position[1], position[2]) if hasattr(position, '__getitem__') else position
        
        self.world.add_component(entity, Transform(position=pos_vec))
        
        # Loot metadata
        self.world.add_component(entity, PickupComponent(
            pickup_radius=1.5,
            color_name=color_name,
            auto_pickup=True
        ))
        
        # Reuse AvatarColors for logic/data consistency (though not strictly for visual anymore)
        color_def = ColorPalette.get_color(color_name)
        if color_def:
             self.world.add_component(entity, AvatarColors(body_color=color_def.rgba))
             
        # Create Visual (if rendering is available)
        if self.base:
            try:
                visual = PickupVisual(self.base.render, color_name)
                visual.root.setPos(pos_vec)
                self.visuals[entity] = visual
            except Exception as e:
                print(f"Failed to create pickup visual: {e}")
             
        # print(f"🎁 Spawned {color_name} swatch at {position}")

    def update(self, dt: float):
        """Check for pickups and animate."""
        # Animate visuals
        for visual in self.visuals.values():
            visual.update(dt)
        
        # Naive O(N^2) pickup check (Player vs All Pickups)
        # In production, use spatial partition or physics events
        
        players = self.world.get_entities_with(AvatarColors, Transform) # Assume players have these
        pickups = self.world.get_entities_with(PickupComponent, Transform)
        
        for p_id in players:
            # Check tag to be sure it's a player?
            # Ideally we'd have a PlayerComponent, but checking against main player tag works for now
            if self.world.get_entity_by_tag("player") != p_id:
                continue
                
            p_transform = self.world.get_component(p_id, Transform)
            p_colors = self.world.get_component(p_id, AvatarColors)
            
            for pickup_id in pickups:
                pickup = self.world.get_component(pickup_id, PickupComponent)
                t_transform = self.world.get_component(pickup_id, Transform)
                
                dist = (p_transform.position - t_transform.position).length()
                if dist <= pickup.pickup_radius:
                    self.collect_pickup(p_id, p_colors, pickup_id, pickup)

    def collect_pickup(self, player_id, player_colors, pickup_id, pickup):
        """Process collection."""
        if pickup.color_name:
            if player_colors.unlock_color(pickup.color_name):
                # print(f"🎉 Unlocked color: {pickup.color_name}!")
                # TODO: Notification UI
                pass
            else:
                pass
                # print(f"Already have {pickup.color_name}")
        
        # Clean up visual
        if pickup_id in self.visuals:
            self.visuals[pickup_id].destroy()
            del self.visuals[pickup_id]
            
        self.world.destroy_entity(pickup_id)
