"""
Projectile System.

Handles movement, collision, and impact of color projectiles.
"""

from engine.ecs.system import System
from engine.components.core import Transform, Health
from engine.components.projectile import ColorProjectileComponent
from engine.components.avatar_colors import AvatarColors
from engine.rendering.pickup_visual import PickupVisual
from engine.color.palette import ColorPalette
from engine.animation.particles import VoxelParticleSystem, create_color_splat
from panda3d.core import LVector3f, LVector4f
from direct.showbase.ShowBase import ShowBase

class ProjectileSystem(System):
    """Manages moving projectiles."""
    
    def __init__(self, world, event_bus, game):
        super().__init__(world, event_bus)
        self.game = game
        self.visuals = {} # entity_id -> NodePath (or visual wrapper)
        # Use passed game instance as base (it inherits ShowBase)
        self.base = game
        
        # Particle system for impact effects
        self.particle_system = VoxelParticleSystem(game.render, max_particles=200) if game else None
            
        self.event_bus.subscribe("spawn_projectile", self.on_spawn_projectile)
            
    def on_spawn_projectile(self, event):
        """Handle request to spawn projectile."""
        # event fields: position, velocity, color_name, owner_id
        entity = self.world.create_entity()
        
        start_pos = event.position
        
        self.world.add_component(entity, Transform(position=start_pos))
        self.world.add_component(entity, ColorProjectileComponent(
            color_name=event.color_name,
            owner_id=event.owner_id,
            velocity=event.velocity
        ))
        
        # Create Visual
        if self.base:
            self._create_visual(entity, event.color_name, start_pos)
            
    def _create_visual(self, entity_id, color_name, pos):
        """Create visual representation (swatch cube)."""
        # Always use PickupVisual for now - reliable and colored
        visual = PickupVisual(self.base.render, color_name)
        visual.root.setScale(0.2)
        visual.root.setPos(pos)
        self.visuals[entity_id] = visual
        print(f"Created visual for projectile at {pos}")
            
    def update(self, dt: float):
        """Update physics and collision."""
        
        projectiles = self.world.get_entities_with(ColorProjectileComponent, Transform)
        
        entities_to_destroy = []
        
        # For collision check
        potential_targets = self.world.get_entities_with(Transform, AvatarColors)
        
        for p_id in projectiles:
            proj = self.world.get_component(p_id, ColorProjectileComponent)
            transform = self.world.get_component(p_id, Transform)
            
            # Update Lifetime
            proj.lifetime -= dt
            if proj.lifetime <= 0:
                entities_to_destroy.append(p_id)
                continue
                
            # Update Physics (Movement + Gravity)
            # Euler integration
            proj.velocity.z -= proj.gravity * dt
            step = proj.velocity * dt
            new_pos = transform.position + step
            
            # Simple ground collision
            # Terrain check? Query terrain system?
            # For now, floor is at Y=0 (Panda Z=0?) actually camp floor is Y+1.
            # Terrain height can be queried if we have access.
            terrain_height = 0 # Default floor
            
            # Using LootSystem's approach, Y is up? No, in standard MyCraft code:
            # VoxelWorldGenerator: grid[(x, h, z)] = block. 
            # Panda defaults: Z is up, Y is depth.
            # My Code: Transform(position=Vector3).
            # Usually we treat Y as Up in voxel worlds (Minecraft style), but Panda renders Z-up.
            # Codebase check: `blocks[(x, y, z)]` in generator.
            # `MeshBuilder`: `v0 = LVector3f(world_x, world_z, y + 1)` (Z is Panda Up)
            # So Y in voxel grid = Z in world.
            
            if new_pos.z < terrain_height:
                 # Hit ground - emit splat particles
                 if self.particle_system:
                     color_def = ColorPalette.get_color(proj.color_name)
                     if color_def:
                         r, g, b, a = color_def.rgba
                         create_color_splat(self.particle_system, new_pos, LVector4f(r, g, b, 1.0))
                 entities_to_destroy.append(p_id)
                 continue
                 
            # Update Transform
            transform.position = new_pos
            
            # Update Visual
            if p_id in self.visuals:
                vis = self.visuals[p_id]
                # If PickupVisual wrapper
                if hasattr(vis, 'root'):
                    vis.root.setPos(new_pos)
                else: # NodePath
                    vis.setPos(new_pos)
            
            # Collision Check vs Players/Enemies
            for t_id in potential_targets:
                if t_id == proj.owner_id:
                    continue
                    
                target_pos = self.world.get_component(t_id, Transform).position
                dist_sq = (target_pos - new_pos).length_squared()
                
                # print(f"DEBUG: PPos: {new_pos}, TPos: {target_pos}, DistSq: {dist_sq}")
                
                # Simple sphere-sphere (radius + radius)
                # Assume target radius 0.5 (player width) + proj radius 0.2
                if dist_sq < (0.7 * 0.7):
                    # Hit! Emit splat particles
                    if self.particle_system:
                        color_def = ColorPalette.get_color(proj.color_name)
                        if color_def:
                            r, g, b, a = color_def.rgba
                            create_color_splat(self.particle_system, new_pos, LVector4f(r, g, b, 1.0))
                    self._on_hit(t_id, proj.color_name)
                    entities_to_destroy.append(p_id)
                    break
                    
        for p_id in entities_to_destroy:
            if p_id in self.visuals:
                vis = self.visuals[p_id]
                if hasattr(vis, 'destroy'):
                    vis.destroy()
                else:
                    vis.removeNode()
                del self.visuals[p_id]
            self.world.destroy_entity(p_id)
        
        # Update particle system
        if self.particle_system:
            self.particle_system.update(dt)
            
    def _on_hit(self, target_id, color_name):
        """Apply paint effect."""
        colors = self.world.get_component(target_id, AvatarColors)
        if colors:
            color_def = ColorPalette.get_color(color_name)
            if color_def:
                colors.apply_temporary_color(color_def.rgba, duration=60.0)
                # print(f"Painted entity {target_id} {color_name}!")
            else:
                 pass
                 # print(f"Failed to find color {color_name} in palette")
