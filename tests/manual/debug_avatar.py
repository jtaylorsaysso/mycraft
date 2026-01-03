"""
Debug script to visualize and inspect VoxelAvatar construction.

Run with: python3 tests/manual/debug_avatar.py
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector3f, LineSegs, NodePath
import sys
import os

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.animation.skeleton import HumanoidSkeleton
from engine.animation.voxel_avatar import VoxelAvatar


class AvatarDebugApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Camera setup
        self.disableMouse()
        self.camera.setPos(0, -8, 2)
        self.camera.lookAt(0, 0, 1)
        
        # Create avatar
        print("\n" + "="*60)
        print("VOXEL AVATAR DEBUG")
        print("="*60)
        
        # Create skeleton first for inspection
        print("\n--- SKELETON CONSTRUCTION ---")
        skeleton = HumanoidSkeleton()
        self._print_skeleton_debug(skeleton)
        
        # Create avatar
        print("\n--- AVATAR CONSTRUCTION ---")
        self.avatar = VoxelAvatar(
            self.render,
            skeleton=skeleton,
            body_color=(0.2, 0.8, 0.2, 1.0),
            validate=True
        )
        self._print_avatar_debug(self.avatar)
        
        # Draw debug axes at origin
        self._draw_axes()
        
        # Draw bone axes for visualization
        self._draw_bone_debug(self.avatar)
        
        # Simple orbit controls
        self.accept('arrow_left', self._orbit, [-5])
        self.accept('arrow_right', self._orbit, [5])
        self.accept('arrow_up', self._raise_cam, [0.5])
        self.accept('arrow_down', self._raise_cam, [-0.5])
        self.accept('=', self._zoom, [-1])
        self.accept('-', self._zoom, [1])
        
        self.orbit_angle = 0
        self.cam_height = 2
        self.cam_dist = 8
        
        print("\n--- CONTROLS ---")
        print("Arrow Left/Right: Orbit camera")
        print("Arrow Up/Down: Raise/lower camera")
        print("+/-: Zoom in/out")
        print("="*60 + "\n")
        
    def _print_skeleton_debug(self, skeleton):
        """Print detailed skeleton information."""
        print(f"\nTotal bones: {len(skeleton.bones)}")
        print(f"Root bone: {skeleton.root.name}, length={skeleton.root.length}")
        
        print("\nBone Hierarchy:")
        self._print_bone_tree(skeleton.root, indent=0)
        
        print("\nBone Transforms (Local):")
        print(f"{'Bone':<20} {'Position':<30} {'Rotation (HPR)':<25} {'Length'}")
        print("-" * 90)
        for name, bone in skeleton.bones.items():
            pos = bone.local_transform.position
            rot = bone.local_transform.rotation
            print(f"{name:<20} ({pos.x:>6.2f}, {pos.y:>6.2f}, {pos.z:>6.2f})      "
                  f"({rot.x:>6.1f}, {rot.y:>6.1f}, {rot.z:>6.1f})    {bone.length:.2f}")
    
    def _print_bone_tree(self, bone, indent):
        """Recursively print bone tree."""
        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        print(f"{prefix}{bone.name} (len={bone.length:.2f})")
        for child in bone.children:
            self._print_bone_tree(child, indent + 1)
    
    def _print_avatar_debug(self, avatar):
        """Print avatar node information."""
        print(f"\nAvatar root: {avatar.root}")
        print(f"Bone nodes created: {len(avatar.bone_nodes)}")
        
        print("\nNode Transforms (World):")
        print(f"{'Node':<20} {'World Position':<30} {'World HPR':<25}")
        print("-" * 75)
        for name, node in avatar.bone_nodes.items():
            pos = node.getPos(self.render)
            hpr = node.getHpr(self.render)
            print(f"{name:<20} ({pos.x:>6.2f}, {pos.y:>6.2f}, {pos.z:>6.2f})      "
                  f"({hpr.x:>6.1f}, {hpr.y:>6.1f}, {hpr.z:>6.1f})")
        
        # Check for visual nodes
        print("\nVisual Geometry Check:")
        for name, node in avatar.bone_nodes.items():
            visual = node.find(f"**/visual_{name}")
            if visual and not visual.isEmpty():
                scale = visual.getScale()
                pos = visual.getPos()
                print(f"  ✓ {name}: visual at pos=({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}), "
                      f"scale=({scale.x:.2f}, {scale.y:.2f}, {scale.z:.2f})")
            else:
                bone = avatar.skeleton.get_bone(name)
                if bone and bone.length > 0.01:
                    print(f"  ✗ {name}: MISSING visual! (bone.length={bone.length:.2f})")
                else:
                    print(f"  - {name}: no visual (length={bone.length if bone else 'N/A'})")
    
    def _draw_axes(self):
        """Draw world axes at origin."""
        lines = LineSegs()
        lines.setThickness(2)
        
        # X axis (red)
        lines.setColor(1, 0, 0, 1)
        lines.moveTo(0, 0, 0)
        lines.drawTo(1, 0, 0)
        
        # Y axis (green)
        lines.setColor(0, 1, 0, 1)
        lines.moveTo(0, 0, 0)
        lines.drawTo(0, 1, 0)
        
        # Z axis (blue)
        lines.setColor(0, 0, 1, 1)
        lines.moveTo(0, 0, 0)
        lines.drawTo(0, 0, 1)
        
        node = lines.create()
        self.render.attachNewNode(node)
    
    def _draw_bone_debug(self, avatar):
        """Draw debug lines showing bone orientations."""
        lines = LineSegs()
        lines.setThickness(1)
        lines.setColor(1, 1, 0, 0.5)  # Yellow, semi-transparent
        
        for name, node in avatar.bone_nodes.items():
            bone = avatar.skeleton.get_bone(name)
            if not bone or bone.length < 0.01:
                continue
            
            # Get world position
            world_pos = node.getPos(self.render)
            
            # Draw line along bone's local Y axis (the bone direction)
            # Transform local Y by node's rotation
            local_y = LVector3f(0, bone.length, 0)
            world_end = node.getRelativePoint(self.render, local_y)
            
            lines.moveTo(world_pos)
            lines.drawTo(world_end)
        
        node = lines.create()
        self.render.attachNewNode(node)
    
    def _orbit(self, delta):
        import math
        self.orbit_angle += delta
        rad = math.radians(self.orbit_angle)
        self.camera.setPos(
            math.sin(rad) * self.cam_dist,
            -math.cos(rad) * self.cam_dist,
            self.cam_height
        )
        self.camera.lookAt(0, 0, 1)
    
    def _raise_cam(self, delta):
        self.cam_height += delta
        self._orbit(0)
    
    def _zoom(self, delta):
        self.cam_dist = max(2, self.cam_dist + delta)
        self._orbit(0)


if __name__ == "__main__":
    app = AvatarDebugApp()
    app.run()
