
from typing import Optional, Dict
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG
from panda3d.core import NodePath, Vec3, Point3, CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay, BitMask32

from engine.editor.workspace import Workspace
from engine.editor.tools.common.voxel_canvas import VoxelCanvas
from engine.editor.tools.common.orbit_camera import OrbitCamera
from engine.editor.tools.common.editor_history import EditorHistory
from engine.editor.tools.common.entity_marker import EntityMarkerManager
from engine.editor.panels.block_palette import BlockPalette
from engine.editor.panels.entity_palette import EntityPalette
from engine.editor.panels.poi_property_panel import POIPropertyPanel
from engine.assets.poi_template import POITemplate
from engine.core.logger import get_logger

logger = get_logger(__name__)

class POIWorkspace(Workspace):
    """Workspace for designing Points of Interest."""
    
    def __init__(self, app):
        super().__init__(app, "POI")
        
        # Core Systems
        self.history = EditorHistory(max_history=50)
        self.camera_controller = OrbitCamera(app)
        
        # Tools
        self.canvas: Optional[VoxelCanvas] = None
        self.markers: Optional[EntityMarkerManager] = None
        
        # UI
        self.block_palette: Optional[BlockPalette] = None
        self.entity_palette: Optional[EntityPalette] = None
        self.properties: Optional[POIPropertyPanel] = None
        
        # State
        self.active_tool = "block_brush" # block_brush, entity_placer, eraser
        self.selected_block_type = "stone_bricks"
        self.selected_entity_type = "skeleton"
        self.current_template_name = "untitled_poi"
        
        # Picking
        self.picker = CollisionTraverser()
        self.picker_queue = CollisionHandlerQueue()
        self.picker_ray = CollisionRay()
        self.picker_node = CollisionNode('mouseRay')
        self.picker_node.setFromCollideMask(BitMask32.allOn())
        self.picker_np = app.camera.attachNewNode(self.picker_node)
        self.picker.addCollider(self.picker_np, self.picker_queue)
        
    def enter(self):
        super().enter()
        self._setup_scene()
        self._build_ui()
        self.camera_controller.enable()
        self.accept("mouse1", self._on_left_click)
        self.accept("mouse3", self._on_right_click)
        # Add frame update for hovering
        # self.app.taskMgr.add(self._update_hover, "poi_hover_task")
        
    def exit(self):
        super().exit()
        self.camera_controller.disable()
        # self.app.taskMgr.remove("poi_hover_task")
        self._cleanup_ui()
        
        if self.canvas:
            self.canvas.cleanup()
            self.canvas = None
        if self.markers:
            self.markers.clear()
            self.markers = None
            
    def _setup_scene(self):
        if not self.canvas:
            self.canvas = VoxelCanvas(self.app)
            # Default floor
            for x in range(-2, 3):
                for z in range(-2, 3):
                    self.canvas.add_voxel_with_type((x, 0, z), "grass", (0.2, 0.8, 0.2, 1))
                    
        if not self.markers:
            self.markers = EntityMarkerManager(self.canvas.root)
            
        # Reparent to app render
        self.canvas.root.reparentTo(self.app.render)
        
    def _build_ui(self):
        # 1. Left Panel - Block Palette
        self.block_palette = BlockPalette(
            parent=self.app.pixel2d,
            on_select_callback=self._on_block_select
        )
        self.block_palette.setPos(-1.4, 0, 0) # Left side
        self.block_palette.setScale(0.8) # Fit height
        
        # 2. Right Panel - Properties
        self.properties = POIPropertyPanel(
            parent=self.app.pixel2d
        )
        self.properties.setPos(1.4, 0, 0)
        self.properties.setScale(0.8)
        
        # 3. Entity Palette (tabbed? or separate?)
        # Let's put it next to Block Palette for now, or toggle
        self.entity_palette = EntityPalette(
            parent=self.app.pixel2d,
            on_select_callback=self._on_entity_select
        )
        self.entity_palette.setPos(-0.9, 0, 0) # Right of block palette
        self.entity_palette.setScale(0.8)
        
        # 4. Toolbar (Top)
        self.toolbar = DirectFrame(
             parent=self.app.aspect2d,
             frameColor=(0.2, 0.2, 0.2, 0.8),
             frameSize=(-0.5, 0.5, -0.05, 0.05),
             pos=(0, 0, 0.85)
        )
        self._add_tool_btn("Save", -0.4, self._on_save, (0.2, 0.6, 0.2, 1))
        self._add_tool_btn("Load", -0.2, self._on_load)
        self._add_tool_btn("Clear", 0.0, self._on_clear, (0.6, 0.2, 0.2, 1))
        self._add_tool_btn("Undo", 0.2, self._on_undo)
        self._add_tool_btn("Redo", 0.4, self._on_redo)
        
    def _add_tool_btn(self, text, x_pos, command, color=(0.5, 0.5, 0.5, 1)):
        DirectButton(
            parent=self.toolbar,
            text=text,
            scale=0.04,
            pos=(x_pos, 0, -0.01),
            command=command,
            frameColor=color,
            relief=DGG.RAISED
        )

    def _cleanup_ui(self):
        if self.block_palette:
            self.block_palette.destroy()
        if self.entity_palette:
            self.entity_palette.destroy()
        if self.properties:
            self.properties.destroy()
        if hasattr(self, 'toolbar'):
            self.toolbar.destroy()

    def update(self, dt: float):
        self.camera_controller.update()
        
    def accept_shortcuts(self):
        self.accept("control-z", self._on_undo)
        self.accept("control-y", self._on_redo)
        self.accept("control-s", self._on_save)
        
    # --- Input Handling ---
    
    def _on_block_select(self, block_name):
        self.active_tool = "block_brush"
        self.selected_block_type = block_name
        logger.info(f"Selected block: {block_name}")
        
    def _on_entity_select(self, entity_type):
        self.active_tool = "entity_placer"
        self.selected_entity_type = entity_type
        logger.info(f"Selected entity: {entity_type}")

    def _get_mouse_ground_pos(self):
        if not self.app.mouseWatcherNode.hasMouse():
            return None
            
        mpos = self.app.mouseWatcherNode.getMouse()
        self.picker_ray.setFromLens(self.app.camNode, mpos.getX(), mpos.getY())
        
        # Simple plane intersection (y=0 approx? No, need full raycast really)
        # But we don't have physics world here.
        # So we collide against the voxel mesh itself?
        # VoxelCanvas builds GeomNode. We need to collide with it.
        # Ensure VoxelCanvas nodes have collide masks?
        
        # Fallback: Plane intersection with Y=0 (Panda Y-up? MyCraft uses Y-up?)
        # MyCraft uses Y-up.
        
        # Ray-Plane intersection
        # Plane normal (0, 1, 0), point (0, 0, 0)
        # Ray origin O, dir D
        
        # But we want to paint ON blocks too.
        # Let's rely on camera distance logic for now or pseudo-raycast
        
        # Wait, MyCraft uses Y-up?
        # Standard Panda: Z-up. 
        # Check voxel_canvas: _build_grid uses XZ plane. Y is unused?
        # lines.moveTo(i, -size, 0) -> X, Y, Z.
        # It draws grid on Z=0? No.
        # "draws a reference grid on the XZ plane" -> typically means Y is up or Y is forward.
        # Let's look at `_build_grid` again.
        # X lines: (i, -size, 0) to (i, size, 0). Varying Y. Constant Z=0.
        # Y lines: (-size, i, 0) to (size, i, 0). Varying X. Constant Z=0.
        # So Grid is on Z=0.
        # MyCraft Engine: Y-up is standard. But voxel world often uses Z-up.
        # `get_spawn_position` returns (x, y, z).
        # Let's use simple plane Z=0 or existing voxel mesh picking if possible.
        
        # For MVP: Raycast to Z-plane at cursor height (for air placement) or existing voxels.
        # Let's implement simple Plane Z=mouse_z?
        
        # HACK: Raycast against the ground plane (Z=0)
        near_point = Point3()
        far_point = Point3()
        self.app.camLens.extrude(mpos, near_point, far_point)
        
        # Transform to world
        near_world = self.app.render.getRelativePoint(self.app.cam, near_point)
        far_world = self.app.render.getRelativePoint(self.app.cam, far_point)
        
        # Ray: P = O + tD
        direction = far_world - near_world
        direction.normalize()
        
        # Intersect with Z=0 plane (or Z=current_layer? defaulting to 0)
        # Normal N=(0,0,1), D=0
        # t = -(O dot N + D) / (Dir dot N)
        # t = -(near_z) / dir_z
        
        if abs(direction.z) < 0.001:
            return None # Parallel
            
        t = -near_world.z / direction.z
        if t < 0:
            return None
            
        hit_pos = near_world + direction * t
        return hit_pos

    def _on_left_click(self):
        pos = self._get_mouse_ground_pos()
        if not pos:
            return
            
        # Snap to grid
        ix, iy, iz = round(pos.x), round(pos.y), round(pos.z)
        # Z should be 0 for ground plane, but we want 3D painting.
        # We need true raycasting against existing blocks to build up.
        # For MVP, let's just use the ground plane intersection and allow stacking with modifier keys?
        # Or just Shift+Click to raise/lower layer?
        
        # Let's assume Z=0 for now.
        
        action_performed = False
        
        if self.active_tool == "block_brush":
            self.canvas.add_voxel_with_type((ix, iy, iz), self.selected_block_type)
            action_performed = True
            
        elif self.active_tool == "entity_placer":
            # Add slightly above
            self.markers.add_marker((ix, iy, iz + 1), self.selected_entity_type)
            action_performed = True
            
        if action_performed:
            # self.history.push(...)
            pass

    def _on_right_click(self):
        pos = self._get_mouse_ground_pos()
        if not pos:
            return
            
        ix, iy, iz = round(pos.x), round(pos.y), round(pos.z)
        
        # Erase
        self.canvas.remove_voxel((ix, iy, iz))
        # Check markers too?
        marker = self.markers.get_marker_at((ix, iy, iz + 1))
        if marker:
            self.markers.remove_marker(marker)
            
    # --- Toolbar Actions ---
    
    def _on_save(self):
        logger.info("Saving POI...")
        template = POITemplate(
            name=self.properties.current_poi_data["name"],
            poi_type=self.properties.current_poi_data["type"],
            biome_affinity=[self.properties.current_poi_data["biome"]],
            blocks=self.canvas.to_poi_blocks(),
            entities=self.markers.to_poi_entities()
        )
        template.calculate_bounds()
        
        filename = template.name.lower().replace(" ", "_")
        self.app.asset_manager.save_poi_template(template, filename)
        logger.info(f"Saved {filename}.mcp")

    def _on_load(self):
        logger.info("Loading POI...(TODO Dialog)")
        # For now, quick load last or specific?
        # Just simple test load
        try:
            filename = self.properties.current_poi_data["name"].lower().replace(" ", "_")
            template = self.app.asset_manager.load_poi_template(filename)
            
            self.canvas.from_poi_blocks(template.blocks)
            self.markers.from_poi_entities(template.entities)
            
            # Restore properties
            self.current_template_name = template.name
            logger.info(f"Loaded {template.name}")
        except Exception as e:
            logger.error(f"Load failed: {e}")

    def _on_clear(self):
        self.canvas.clear()
        self.markers.clear()
        
    def _on_undo(self): 
        # TODO connection to EditorHistory
        logger.info("Undo not yet implemented")

    def _on_redo(self):
        logger.info("Redo not yet implemented")
