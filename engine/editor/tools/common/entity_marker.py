
from typing import List, Tuple, Optional, Dict
from panda3d.core import NodePath, TextNode, Vec3, Vec4
from direct.showbase.DirectObject import DirectObject

class EntityMarker(DirectObject):
    """Visual marker for entity spawn point."""
    
    # Colors by category
    COLORS = {
        "enemy": (0.9, 0.2, 0.2, 1),      # Red
        "friendly": (0.2, 0.8, 0.2, 1),   # Green
        "interactive": (0.2, 0.6, 1.0, 1), # Blue
        "marker": (1.0, 1.0, 0.2, 1),     # Yellow
        "default": (0.8, 0.8, 0.8, 1)     # Grey
    }
    
    def __init__(self, parent: NodePath, position: Tuple[int, int, int], entity_type: str, category: str = "default"):
        self.entity_type = entity_type
        self.category = category
        self.position = Vec3(position)
        
        # Root node
        self.root = parent.attachNewNode(f"marker_{entity_type}")
        self.root.setPos(self.position)
        
        # Determine color
        self.color = self.COLORS.get(category, self.COLORS["default"])
        
        # 3D Visual (simple sphere)
        # Using built-in models if available, or just a small point
        # For now, we'll try to load a smiley or simple shape, or generate one
        loader = base.loader
        try:
            self.model = loader.loadModel("models/misc/sphere")
        except:
            self.model = loader.loadModel("models/box") # Fallback
            
        self.model.reparentTo(self.root)
        self.model.setScale(0.3)
        self.model.setColor(self.color)
        
        # Label (always face camera)
        self.text_node = TextNode(f"label_{entity_type}")
        self.text_node.setText(entity_type)
        self.text_node.setAlign(TextNode.ACenter)
        self.text_node.setTextColor(1, 1, 1, 1)
        self.text_node.setShadow(0, 0, 0, 1)
        self.text_node.setShadowColor(0, 0, 0, 0.5)
        
        self.label = self.root.attachNewNode(self.text_node)
        self.label.setScale(0.2)
        self.label.setPos(0, 0, 0.5)
        self.label.setBillboardPointEye()
        
        # Collision for picking (sphere)
        # Assuming picking logic will raycast against this node
        self.model.setTag("entity_marker", "true")
        self.selected = False
        
    def set_position(self, pos: Tuple[float, float, float]):
        """Update position."""
        self.position = Vec3(pos)
        self.root.setPos(self.position)
        
    def set_selected(self, is_selected: bool):
        """Highlight selection."""
        self.selected = is_selected
        if is_selected:
            self.model.setColor(1, 1, 1, 1) # White highlight
        else:
            self.model.setColor(self.color)
            
    def cleanup(self):
        """Remove from scene."""
        self.root.removeNode()


class EntityMarkerManager:
    """Manages all entity markers in POI workspace."""
    
    def __init__(self, parent_node: NodePath):
        self.root = parent_node.attachNewNode("EntityMarkers")
        self.markers: List[EntityMarker] = []
        
    def add_marker(self, pos: Tuple[int, int, int], entity_type: str, category: str = "default") -> EntityMarker:
        """Create a new marker."""
        marker = EntityMarker(self.root, pos, entity_type, category)
        self.markers.append(marker)
        return marker
        
    def remove_marker(self, marker: EntityMarker):
        """Remove a marker."""
        if marker in self.markers:
            marker.cleanup()
            self.markers.remove(marker)
            
    def get_marker_at(self, pos: Tuple[int, int, int], tolerance: float = 0.5) -> Optional[EntityMarker]:
        """Find marker near position."""
        target = Vec3(pos)
        for m in self.markers:
            dist = (m.position - target).length()
            if dist < tolerance:
                return m
        return None
        
    def to_poi_entities(self) -> List[Dict]:
        """Export entities for POIData."""
        entities = []
        for m in self.markers:
            # Snap to integer for export
            entities.append({
                "type": m.entity_type,
                "x": int(round(m.position.x)),
                "y": int(round(m.position.y)),
                "z": int(round(m.position.z)),
                "properties": {} # Future expansion
            })
        return entities
        
    def from_poi_entities(self, entities: List[Dict]):
        """Import entities from POIData."""
        self.clear()
        
        # Map common types to categories
        categories = {
            "skeleton": "enemy",
            "zombie": "enemy",
            "chest": "interactive",
            "spawn": "marker"
        }
        
        for e in entities:
            etype = e["type"]
            cat = categories.get(etype, "default")
            self.add_marker((e["x"], e["y"], e["z"]), etype, cat)
            
    def clear(self):
        """Remove all markers."""
        for m in self.markers:
            m.cleanup()
        self.markers.clear()
