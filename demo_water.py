#!/usr/bin/env python3
"""Interactive demo for Phase 6a: Jelly Water System.

Standalone demo with direct camera controls (no ECS).
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector3f, WindowProperties, TransparencyAttrib
from engine.rendering.mesh import MeshBuilder
from engine.rendering.shaders import WATER_WOBBLE_SHADER

class WaterDemo(ShowBase):
    """Standalone water demo with free-floating camera."""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        print("=== MyCraft - Jelly Water Demo ===\n")
        
        # Camera setup
        self.camera_pos = LVector3f(15, 8, 8)
        self.camera_hpr = LVector3f(225, -20, 0)  # Look toward water pool
        self.camera.setPos(self.camera_pos)
        self.camera.setHpr(self.camera_hpr)
        
        # Movement speed
        self.move_speed = 10.0
        self.turn_speed = 50.0
        
        # Key tracking
        self.keys = {
            'w': False, 's': False, 'a': False, 'd': False,
            'space': False, 'shift': False,
            'arrow_up': False, 'arrow_down': False,
            'arrow_left': False, 'arrow_right': False
        }
        
        # Setup input
        self.setup_input()
        
        # Setup scene
        self.setup_scene()
        
        # Generate water
        self.setup_water()
        
        # Add update task
        self.taskMgr.add(self.update_task, "update")
        
        # Print instructions
        self.print_instructions()
    
    def setup_scene(self):
        """Setup basic scene with ground and lighting."""
        from panda3d.core import AmbientLight, DirectionalLight, CardMaker
        
        # Set background color (sky blue)
        self.setBackgroundColor(0.5, 0.7, 1.0)
        
        # Add ambient light
        alight = AmbientLight('ambient')
        alight.setColor((0.6, 0.6, 0.6, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        # Add directional light (sun)
        dlight = DirectionalLight('sun')
        dlight.setColor((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -60, 0)
        self.render.setLight(dlnp)
        
        # Create simple ground plane for reference
        cm = CardMaker('ground')
        cm.setFrame(-50, 50, -50, 50)
        ground = self.render.attachNewNode(cm.generate())
        ground.setPos(0, 0, -0.1)  # Slightly below water
        ground.setP(-90)  # Rotate to be horizontal
        ground.setColor(0.3, 0.5, 0.2, 1)  # Green grass color
        
        print("✓ Scene setup complete (ground + lighting)")
    
    def setup_input(self):
        """Setup keyboard controls."""
        # Movement keys
        self.accept('w', self.set_key, ['w', True])
        self.accept('w-up', self.set_key, ['w', False])
        self.accept('s', self.set_key, ['s', True])
        self.accept('s-up', self.set_key, ['s', False])
        self.accept('a', self.set_key, ['a', True])
        self.accept('a-up', self.set_key, ['a', False])
        self.accept('d', self.set_key, ['d', True])
        self.accept('d-up', self.set_key, ['d', False])
        
        # Vertical movement
        self.accept('space', self.set_key, ['space', True])
        self.accept('space-up', self.set_key, ['space', False])
        self.accept('shift', self.set_key, ['shift', True])
        self.accept('shift-up', self.set_key, ['shift', False])
        
        # Arrow keys for camera rotation
        self.accept('arrow_up', self.set_key, ['arrow_up', True])
        self.accept('arrow_up-up', self.set_key, ['arrow_up', False])
        self.accept('arrow_down', self.set_key, ['arrow_down', True])
        self.accept('arrow_down-up', self.set_key, ['arrow_down', False])
        self.accept('arrow_left', self.set_key, ['arrow_left', True])
        self.accept('arrow_left-up', self.set_key, ['arrow_left', False])
        self.accept('arrow_right', self.set_key, ['arrow_right', True])
        self.accept('arrow_right-up', self.set_key, ['arrow_right', False])
        
        # Exit
        self.accept('escape', self.quit_demo)
    
    def set_key(self, key, value):
        """Update key state."""
        self.keys[key] = value
    
    def quit_demo(self):
        """Exit the demo."""
        print("\nExiting demo...")
        import sys
        sys.exit(0)
    
    def setup_water(self):
        """Generate water mesh."""
        print("Generating water mesh...")
        
        # Create water blocks (8x8 pool at ground level)
        water_blocks = []
        for x in range(4, 12):
            for y in range(4, 12):
                water_blocks.append((x, 0, y))  # Local coords in chunk 0,0
        
        # Build water mesh
        water_node = MeshBuilder.build_water_mesh(
            water_blocks=water_blocks,
            chunk_x=0,
            chunk_z=0,
            chunk_size=16
        )
        
        if water_node:
            # Attach to scene
            self.water_np = self.render.attachNewNode(water_node)
            
            # Apply wobble shader
            self.water_np.setShader(WATER_WOBBLE_SHADER)
            self.water_np.setShaderInput("time", 0.0)
            self.water_np.setShaderInput("wobble_frequency", 2.0)
            self.water_np.setShaderInput("wobble_amplitude", 0.08)
            self.water_np.setShaderInput("water_alpha", 0.7)
            
            # Enable transparency
            self.water_np.setTransparency(TransparencyAttrib.MAlpha)
            self.water_np.setBin("transparent", 0)
            self.water_np.setDepthWrite(False)
            
            self.water_time = 0.0
            
            print(f"✓ Water mesh created with {len(water_blocks)} blocks")
        else:
            print("✗ Failed to create water mesh")
    
    def update_task(self, task):
        """Update camera and water animation."""
        dt = globalClock.getDt()
        
        # Update water wobble time
        self.water_time += dt
        if hasattr(self, 'water_np') and not self.water_np.isEmpty():
            self.water_np.setShaderInput("time", self.water_time)
        
        # Get current camera position and orientation
        current_pos = self.camera.getPos()
        current_hpr = self.camera.getHpr()
        
        # Camera movement
        move_vec = LVector3f(0, 0, 0)
        
        # Forward/backward (relative to camera heading)
        if self.keys['w']:
            move_vec.y += 1
        if self.keys['s']:
            move_vec.y -= 1
        
        # Strafe left/right
        if self.keys['a']:
            move_vec.x -= 1
        if self.keys['d']:
            move_vec.x += 1
        
        # Up/down
        if self.keys['space']:
            move_vec.z += 1
        if self.keys['shift']:
            move_vec.z -= 1
        
        # Apply movement (relative to camera orientation)
        if move_vec.length() > 0:
            move_vec.normalize()
            # Transform movement to world space based on camera heading
            h = current_hpr.x
            import math
            rad = math.radians(h)
            
            world_move = LVector3f(
                move_vec.x * math.cos(rad) - move_vec.y * math.sin(rad),
                move_vec.x * math.sin(rad) + move_vec.y * math.cos(rad),
                move_vec.z
            )
            
            new_pos = current_pos + world_move * self.move_speed * dt
            self.camera.setPos(new_pos)
        
        # Camera rotation with arrow keys
        new_hpr = LVector3f(current_hpr)
        
        if self.keys['arrow_left']:
            new_hpr.x += self.turn_speed * dt
        if self.keys['arrow_right']:
            new_hpr.x -= self.turn_speed * dt
        if self.keys['arrow_up']:
            new_hpr.y += self.turn_speed * dt
        if self.keys['arrow_down']:
            new_hpr.y -= self.turn_speed * dt
        
        # Clamp pitch
        new_hpr.y = max(-89, min(89, new_hpr.y))
        
        self.camera.setHpr(new_hpr)
        
        # Debug: Print camera position every 2 seconds
        if not hasattr(self, 'last_debug_time'):
            self.last_debug_time = 0
        
        self.last_debug_time += dt
        if self.last_debug_time > 2.0:
            pos = self.camera.getPos()
            hpr = self.camera.getHpr()
            print(f"Camera: Pos=({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}), HPR=({hpr.x:.1f}, {hpr.y:.1f}, {hpr.z:.1f})")
            self.last_debug_time = 0
        
        return task.cont
    
    def print_instructions(self):
        """Print usage instructions."""
        print("\n📍 Water Location:")
        print("   X: 4 to 12")
        print("   Y: 4 to 12")
        print("   Z: 0 (ground level)")
        print("\n🎮 Controls:")
        print("   W/S          - Move forward/backward")
        print("   A/D          - Strafe left/right")
        print("   Space/Shift  - Move up/down")
        print("   Arrow Keys   - Rotate camera")
        print("   ESC          - Exit demo")
        print("\n🌊 What to look for:")
        print("   • Semi-transparent cyan-blue water")
        print("   • Wobbling/jelly-like animation")
        print("   • Each block wobbles independently")
        print("\n💡 Tip: Use arrow keys to look around, WASD to fly closer!")
        print("\nDemo running... Press ESC to exit.\n")

if __name__ == "__main__":
    demo = WaterDemo()
    demo.run()
