"""
Interaction System for detecting and interacting with world objects like chests.
"""
from engine.ecs.system import System
from engine.components.core import Transform
from engine.components.chest import ChestComponent
from panda3d.core import CollisionRay, CollisionNode, CollisionTraverser, CollisionHandlerQueue, BitMask32
from direct.showbase.ShowBase import ShowBase


class InteractionSystem(System):
    """Handles player interaction with world objects via raycast."""
    
    def __init__(self, world, event_bus, camera, game):
        super().__init__(world, event_bus)
        self.camera = camera
        self.game = game
        self.base = game  # The game instance is the ShowBase
        self.interaction_range = 5.0  # blocks
        self.last_targeted_chest = None
        
        # Raycast setup
        self.ray = CollisionRay()
        self.ray_node = CollisionNode('interaction_ray')
        self.ray_node.addSolid(self.ray)
        self.ray_node.setFromCollideMask(BitMask32.bit(1))  # Collide with terrain
        self.ray_node.setIntoCollideMask(BitMask32.allOff())
        
        self.traverser = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        
    def initialize(self):
        """Initialize the system."""
        try:
            # self.base already set in __init__
            
            # Attach ray to camera
            self.ray_np = self.camera.attachNewNode(self.ray_node)
            self.traverser.addCollider(self.ray_np, self.handler)
            
            # Listen for interaction key
            self.base.accept("e", self._on_interact_key)
            
        except Exception as e:
            print(f"InteractionSystem initialization warning: {e}")
    
    def _on_interact_key(self):
        """Handle E key press for interaction."""
        if self.last_targeted_chest:
            # Publish event for UI to handle
            self.event_bus.publish("chest_opened", chest_entity=self.last_targeted_chest)
    
    def update(self, dt: float):
        """Update interaction detection."""
        if not self.camera:
            return
        
        # Set ray from camera forward
        self.ray.setOrigin(self.camera.getPos(self.base.render))
        self.ray.setDirection(self.camera.getQuat(self.base.render).getForward())
        
        # Perform raycast
        self.traverser.traverse(self.base.render)
        
        # Check if we hit a chest block
        self.last_targeted_chest = None
        
        if self.handler.getNumEntries() > 0:
            self.handler.sortEntries()
            entry = self.handler.getEntry(0)
            hit_point = entry.getSurfacePoint(self.base.render)
            
            # Calculate distance
            cam_pos = self.camera.getPos(self.base.render)
            distance = (hit_point - cam_pos).length()
            
            if distance <= self.interaction_range:
                # Convert hit point to block coordinates
                # Offset slightly in the direction of the normal to get the block we're looking at
                normal = entry.getSurfaceNormal(self.base.render)
                block_pos = hit_point + normal * 0.1
                
                bx = int(block_pos.x)
                by = int(block_pos.y)
                bz = int(block_pos.z)
                
                # Check if there's a chest entity at this position
                for entity_id in self.world.get_entities_with(ChestComponent):
                    chest = self.world.get_component(entity_id, ChestComponent)
                    if chest.position == (bx, by, bz) and not chest.is_open:
                        self.last_targeted_chest = entity_id
                        break
    
    def cleanup(self):
        """Clean up the system."""
        if self.base:
            self.base.ignore("e")
        if self.ray_np:
            self.ray_np.removeNode()
