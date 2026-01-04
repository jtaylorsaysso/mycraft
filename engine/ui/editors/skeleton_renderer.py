"""
Skeleton visualization component for model editor.

Renders skeleton wireframe, joint markers, and bone axes for debugging
and visual editing of character skeletons.
"""

from typing import Optional
from panda3d.core import NodePath, LineSegs, LVector3f
from engine.animation.skeleton import HumanoidSkeleton, Bone
from engine.animation.voxel_avatar import VoxelAvatar


class SkeletonRenderer:
    """Renders skeleton wireframe and joint markers.
    
    Provides visual debugging and editing aids for character skeletons,
    including bone lines, joint spheres, and coordinate axes.
    """
    
    def __init__(self, parent_node: NodePath):
        """Initialize skeleton renderer.
        
        Args:
            parent_node: Parent node to attach visualization to
        """
        self.parent_node = parent_node
        self.root = parent_node.attachNewNode("SkeletonRenderer")
        
        # Visualization nodes
        self.bone_lines_node: Optional[NodePath] = None
        self.axes_node: Optional[NodePath] = None
        self.highlight_node: Optional[NodePath] = None
        
        # State
        self.skeleton: Optional[HumanoidSkeleton] = None
        self.bone_nodes: dict[str, NodePath] = {}
        self.highlighted_bone: Optional[str] = None
        self.visible = True
        
    def set_skeleton(self, skeleton: HumanoidSkeleton, bone_nodes: Optional[dict[str, NodePath]] = None):
        """Set the skeleton to visualize.
        
        Args:
            skeleton: Skeleton to render
            bone_nodes: Optional dict of bone NodePaths for world transforms
        """
        self.skeleton = skeleton
        self.bone_nodes = bone_nodes or {}
        self._rebuild_visualization()
        
    def update_from_avatar(self, avatar: VoxelAvatar):
        """Update visualization from a VoxelAvatar.
        
        Args:
            avatar: Avatar to extract skeleton and nodes from
        """
        self.set_skeleton(avatar.skeleton, avatar.bone_nodes)
        
    def highlight_bone(self, bone_name: Optional[str]):
        """Highlight a specific bone.
        
        Args:
            bone_name: Name of bone to highlight, or None to clear
        """
        self.highlighted_bone = bone_name
        self._rebuild_highlight()
        
    def set_visible(self, visible: bool):
        """Set visibility of skeleton overlay.
        
        Args:
            visible: Whether skeleton should be visible
        """
        self.visible = visible
        if visible:
            self.root.show()
        else:
            self.root.hide()
            
    def cleanup(self):
        """Remove all visualization nodes."""
        if self.root:
            self.root.removeNode()
            self.root = None
            
    def _rebuild_visualization(self):
        """Rebuild all visualization geometry."""
        self._clear_nodes()
        
        if not self.skeleton:
            return
            
        self._draw_bone_lines()
        self._draw_world_axes()
        
    def _clear_nodes(self):
        """Clear existing visualization nodes."""
        if self.bone_lines_node:
            self.bone_lines_node.removeNode()
            self.bone_lines_node = None
            
        if self.axes_node:
            self.axes_node.removeNode()
            self.axes_node = None
            
        if self.highlight_node:
            self.highlight_node.removeNode()
            self.highlight_node = None
            
    def _draw_bone_lines(self):
        """Draw lines showing bone directions and hierarchy."""
        if not self.skeleton or not self.bone_nodes:
            return
            
        lines = LineSegs()
        lines.setThickness(1)
        lines.setColor(1, 1, 0, 0.5)  # Yellow, semi-transparent
        
        for name, node in self.bone_nodes.items():
            bone = self.skeleton.get_bone(name)
            if not bone or bone.length < 0.01:
                continue
                
            # Get world position of bone start
            world_pos = node.getPos(self.parent_node)
            
            # Draw line along bone's local Y axis (bone direction)
            local_y = LVector3f(0, bone.length, 0)
            world_end = node.getRelativePoint(self.parent_node, local_y)
            
            lines.moveTo(world_pos)
            lines.drawTo(world_end)
            
        node = lines.create()
        self.bone_lines_node = self.root.attachNewNode(node)
        
    def _draw_world_axes(self):
        """Draw world coordinate axes at origin."""
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
        self.axes_node = self.root.attachNewNode(node)
        
    def _rebuild_highlight(self):
        """Rebuild highlight visualization for selected bone."""
        if self.highlight_node:
            self.highlight_node.removeNode()
            self.highlight_node = None
            
        if not self.highlighted_bone or not self.skeleton or not self.bone_nodes:
            return
            
        bone = self.skeleton.get_bone(self.highlighted_bone)
        if not bone or self.highlighted_bone not in self.bone_nodes:
            return
            
        node = self.bone_nodes[self.highlighted_bone]
        
        lines = LineSegs()
        lines.setThickness(3)
        lines.setColor(0, 1, 1, 1)  # Cyan, fully opaque
        
        # Draw highlighted bone line
        world_pos = node.getPos(self.parent_node)
        
        if bone.length > 0.01:
            local_y = LVector3f(0, bone.length, 0)
            world_end = node.getRelativePoint(self.parent_node, local_y)
            
            lines.moveTo(world_pos)
            lines.drawTo(world_end)
            
        # Draw local axes at bone origin
        axis_length = 0.3
        
        # Local X (red)
        lines.setColor(1, 0.5, 0.5, 1)
        local_x = LVector3f(axis_length, 0, 0)
        world_x = node.getRelativePoint(self.parent_node, local_x)
        lines.moveTo(world_pos)
        lines.drawTo(world_x)
        
        # Local Y (green) - bone direction
        lines.setColor(0.5, 1, 0.5, 1)
        local_y_axis = LVector3f(0, axis_length, 0)
        world_y = node.getRelativePoint(self.parent_node, local_y_axis)
        lines.moveTo(world_pos)
        lines.drawTo(world_y)
        
        # Local Z (blue)
        lines.setColor(0.5, 0.5, 1, 1)
        local_z = LVector3f(0, 0, axis_length)
        world_z = node.getRelativePoint(self.parent_node, local_z)
        lines.moveTo(world_pos)
        lines.drawTo(world_z)
        
        highlight = lines.create()
        self.highlight_node = self.root.attachNewNode(highlight)
