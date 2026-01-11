"""
POI Workspace - Enhanced Block Builder for Points of Interest.

Features:
- Accurate voxel picking via collision raycasting
- Ghost block preview for placement feedback
- Layer controls for Y-level editing
- Multiple tool modes (brush, line, fill, eraser)
"""

from typing import Optional, Dict, Tuple, List
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG
from panda3d.core import NodePath, Vec3, Point3

from engine.editor.workspace import Workspace
from engine.editor.tools.common.voxel_canvas import VoxelCanvas
from engine.editor.tools.common.voxel_picker import VoxelPicker, VoxelPickResult
from engine.editor.tools.common.block_preview import BlockPreview, SelectionHighlight
from engine.editor.tools.common.orbit_camera import OrbitCamera
from engine.editor.tools.common.editor_history import EditorHistory, EditorCommand
from engine.editor.ui.toast_notification import ToastNotification
from engine.editor.ui.confirmation_dialog import ConfirmationDialog
from engine.editor.tools.common.entity_marker import EntityMarkerManager
from engine.editor.panels.block_palette import BlockPalette
from engine.editor.panels.entity_palette import EntityPalette
from engine.editor.panels.poi_property_panel import POIPropertyPanel
from engine.editor.panels.layer_control import LayerControl
from engine.editor.panels.tool_mode_panel import ToolModePanel
from engine.assets.poi_template import POITemplate
from engine.core.logger import get_logger

logger = get_logger(__name__)


class POIWorkspace(Workspace):
    """Workspace for designing Points of Interest with enhanced block building."""
    
    def __init__(self, app):
        super().__init__(app, "POI")
        
        # Core Systems
        self.history = EditorHistory(max_history=50)
        self.camera_controller = OrbitCamera(app)
        
        # Voxel Systems
        self.canvas: Optional[VoxelCanvas] = None
        self.picker: Optional[VoxelPicker] = None
        self.preview: Optional[BlockPreview] = None
        self.highlight: Optional[SelectionHighlight] = None
        self.markers: Optional[EntityMarkerManager] = None
        
        # UI Panels
        self.block_palette: Optional[BlockPalette] = None
        self.entity_palette: Optional[EntityPalette] = None
        self.properties: Optional[POIPropertyPanel] = None
        self.layer_control: Optional[LayerControl] = None
        self.tool_panel: Optional[ToolModePanel] = None
        
        # State
        self.active_tool = "brush"
        self.selected_block_type = "stone_bricks"
        self.selected_entity_type = "skeleton"
        self.current_layer = 0
        self.current_template_name = "untitled_poi"
        
        # Dirty state tracking
        self._dirty = False
        self._confirm_dialog = None
        
        # Line tool state
        self._line_start: Optional[Tuple[int, int, int]] = None
        
        # Track if hover task is active
        self._hover_task = None
        
    def enter(self):
        """Called when workspace becomes active."""
        super().enter()
        self._setup_scene()
        self._build_ui()
        self.camera_controller.enable()
        
        # Input bindings
        self.accept("mouse1", self._on_left_click)
        self.accept("mouse1-up", self._on_left_release)
        # Note: Right click (mouse3) is reserved for OrbitCamera navigation
        
        # Start hover tracking
        self._hover_task = self.app.taskMgr.add(self._update_hover, "poi_hover_task")
        
    def exit(self):
        """Called when leaving workspace."""
        super().exit()
        self.camera_controller.disable()
        
        if self._hover_task:
            self.app.taskMgr.remove("poi_hover_task")
            self._hover_task = None
            
        self._cleanup_ui()
        self._cleanup_scene()
        
    def _setup_scene(self):
        """Initialize the 3D scene components."""
        if not self.canvas:
            self.canvas = VoxelCanvas(self.app)
            self._create_base_floor()
                    
        if not self.picker:
            self.picker = VoxelPicker(self.app)
            self.picker.set_parent(self.canvas.root)
            self.picker.sync_with_canvas(self.canvas.voxels)
            
        if not self.preview:
            self.preview = BlockPreview(self.canvas.root)
            
        if not self.highlight:
            self.highlight = SelectionHighlight(self.canvas.root)
            
        if not self.markers:
            self.markers = EntityMarkerManager(self.canvas.root)
            
        # Attach to render
        self.canvas.root.reparentTo(self.app.render)
        
    def _cleanup_scene(self):
        """Clean up 3D scene components."""
        if self.preview:
            self.preview.cleanup()
            self.preview = None
        if self.highlight:
            self.highlight.cleanup()
            self.highlight = None
        if self.picker:
            self.picker.cleanup()
            self.picker = None
        if self.canvas:
            self.canvas.cleanup()
            self.canvas = None
        if self.markers:
            self.markers.clear()
            self.markers = None
            
    def _build_ui(self):
        """Build UI panels."""
        # 1. Block Palette (left side)
        self.block_palette = BlockPalette(
            parent=self.app.aspect2d,
            on_select_callback=self._on_block_select
        )
        self.block_palette.setPos(-1.4, 0, 0)
        
        # 2. Tool Mode Panel (top center)
        self.tool_panel = ToolModePanel(
            parent=self.app.aspect2d,
            on_tool_change=self._on_tool_change
        )
        self.tool_panel.setPos(0, 0, 0.85)
        
        # 3. Layer Control (top right of tool panel)
        self.layer_control = LayerControl(
            parent=self.app.aspect2d,
            on_layer_change=self._on_layer_change,
            min_layer=0,
            max_layer=15
        )
        self.layer_control.setPos(0.5, 0, 0.85)
        
        # 4. Properties Panel (right side)
        self.properties = POIPropertyPanel(
            parent=self.app.aspect2d,
            asset_manager=self.app.asset_manager,
            on_load=self._on_template_load_request,
            on_new=self._on_template_new_request,
            on_save=self._on_save,
            on_size_change=self._on_canvas_size_change
        )
        self.properties.setPos(1.4, 0, 0)
        
        # 5. Entity Palette (below block palette)
        self.entity_palette = EntityPalette(
            parent=self.app.aspect2d,
            on_select_callback=self._on_entity_select
        )
        self.entity_palette.setPos(-1.4, 0, -0.6)
        self.entity_palette.setScale(0.8)
        
        # 6. Toolbar (bottom)
        self.toolbar = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0.2, 0.2, 0.2, 0.8),
            frameSize=(-0.5, 0.5, -0.05, 0.05),
            pos=(0, 0, -0.85)
        )
        self._add_tool_btn("Save", -0.4, self._on_save, (0.2, 0.5, 0.2, 1))
        self._add_tool_btn("Load", -0.2, self._on_load)
        self._add_tool_btn("Clear", 0.0, self._on_clear, (0.5, 0.2, 0.2, 1))
        self._add_tool_btn("Undo", 0.2, self._on_undo)
        self._add_tool_btn("Redo", 0.4, self._on_redo)
        
    def _add_tool_btn(self, text, x_pos, command, color=(0.4, 0.4, 0.4, 1)):
        """Helper to add toolbar buttons."""
        DirectButton(
            parent=self.toolbar,
            text=text,
            scale=0.04,
            pos=(x_pos, 0, -0.01),
            command=command,
            frameColor=color,
            relief=DGG.FLAT
        )
        
    def _cleanup_ui(self):
        """Clean up UI panels."""
        for panel in [self.block_palette, self.entity_palette, 
                      self.properties, self.layer_control, self.tool_panel]:
            if panel:
                panel.destroy()
        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.destroy()
            
    def update(self, dt: float):
        """Per-frame update."""
        self.camera_controller.update()
        
    def accept_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.accept("control-z", self._on_undo)
        self.accept("control-y", self._on_redo)
        self.accept("control-s", self._on_save)
        self.accept("1", lambda: self.tool_panel.set_tool("brush"))
        self.accept("2", lambda: self.tool_panel.set_tool("line"))
        self.accept("3", lambda: self.tool_panel.set_tool("fill"))
        self.accept("4", lambda: self.tool_panel.set_tool("eraser"))
        # Layer shortcuts
        self.accept("[", lambda: self.layer_control._layer_down())
        self.accept("]", lambda: self.layer_control._layer_up())
        
    # --- Callbacks ---
    
    def _on_block_select(self, block_name: str):
        """Handle block palette selection."""
        self.selected_block_type = block_name
        if self.active_tool == "eraser":
            self.tool_panel.set_tool("brush")
        self._update_preview_color()
        logger.info(f"Selected block: {block_name}")
        
    def _on_entity_select(self, entity_type: str):
        """Handle entity palette selection."""
        self.selected_entity_type = entity_type
        self.active_tool = "entity_placer"
        logger.info(f"Selected entity: {entity_type}")
        
    def _on_tool_change(self, tool_id: str):
        """Handle tool mode change."""
        self.active_tool = tool_id
        self._line_start = None  # Reset line tool state
        self._update_preview_color()
        logger.info(f"Tool: {tool_id}")
        
    def _on_layer_change(self, layer: int):
        """Handle layer change."""
        self.current_layer = layer
        logger.info(f"Layer: {layer}")
        
    def _on_canvas_size_change(self, size: int):
        """Handle canvas size change from properties panel."""
        if self.canvas:
            self.canvas.set_size(size)
            self.canvas.clear()
            self._create_base_floor()
            if self.picker:
                self.picker.sync_with_canvas(self.canvas.voxels)
            self.history.clear()
            logger.info(f"Canvas size changed to {size}")
        
    def _update_preview_color(self):
        """Update preview block color based on selected block."""
        if not self.preview:
            return
        if self.active_tool == "eraser":
            self.preview.set_color((1.0, 0.3, 0.3, 0.4))  # Red for eraser
        else:
            # Get block color
            from games.voxel_world.blocks.blocks import BlockRegistry
            try:
                block = BlockRegistry.get_block(self.selected_block_type)
                color = block.color if len(block.color) == 4 else (*block.color, 0.4)
                self.preview.set_color((*color[:3], 0.4))
            except Exception:
                self.preview.set_color((0.5, 0.7, 1.0, 0.4))
                
    # --- Hover Tracking ---
    
    def _update_hover(self, task):
        """Update hover state each frame."""
        if not self.picker or not self.canvas:
            return task.cont
            
        pick_result = self.picker.pick()
        
        if pick_result:
            # Show selection highlight on hovered block
            self.highlight.show_at(pick_result.hit_pos)
            
            # Show preview at adjacent position (for placement tools)
            if self.active_tool in ("brush", "line", "fill"):
                adj_pos = pick_result.adjacent_pos
                self.preview.show_at(adj_pos)
            elif self.active_tool == "eraser":
                # Preview on the block itself for eraser
                self.preview.show_at(pick_result.hit_pos)
            else:
                self.preview.hide()
        else:
            self.highlight.hide()
            self.preview.hide()
            
        return task.cont
        
    # --- Click Handling ---
    
    def _on_left_click(self):
        """Handle left mouse click."""
        if not self.picker:
            return
            
        pick_result = self.picker.pick()
        
        if self.active_tool == "brush":
            self._do_brush_place(pick_result)
        elif self.active_tool == "line":
            self._do_line_start(pick_result)
        elif self.active_tool == "fill":
            self._do_fill(pick_result)
        elif self.active_tool == "eraser":
            self._do_erase(pick_result)
        elif self.active_tool == "entity_placer":
            self._do_place_entity(pick_result)
            
    def _on_left_release(self):
        """Handle left mouse release (for line tool)."""
        if self.active_tool == "line" and self._line_start:
            pick_result = self.picker.pick() if self.picker else None
            self._do_line_end(pick_result)
            
    # --- Tool Actions ---
    
    def _do_brush_place(self, pick_result: Optional[VoxelPickResult]):
        """Place a single block."""
        if not pick_result:
            return
            
        pos = pick_result.adjacent_pos
        self._add_block(pos, self.selected_block_type)
        
    def _do_line_start(self, pick_result: Optional[VoxelPickResult]):
        """Start drawing a line."""
        if not pick_result:
            return
        self._line_start = pick_result.adjacent_pos
        
    def _do_line_end(self, pick_result: Optional[VoxelPickResult]):
        """Finish drawing a line."""
        if not self._line_start:
            return
            
        if pick_result:
            end_pos = pick_result.adjacent_pos
        else:
            end_pos = self._line_start
            
        # Draw line using Bresenham-style stepping
        positions = self._line_positions(self._line_start, end_pos)
        for pos in positions:
            self._add_block(pos, self.selected_block_type)
            
        self._line_start = None
        
    def _line_positions(
        self, 
        start: Tuple[int, int, int], 
        end: Tuple[int, int, int]
    ) -> List[Tuple[int, int, int]]:
        """Generate positions along a 3D line."""
        positions = []
        
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        dz = abs(end[2] - start[2])
        
        steps = max(dx, dy, dz, 1)
        
        for i in range(steps + 1):
            t = i / steps if steps > 0 else 0
            x = round(start[0] + t * (end[0] - start[0]))
            y = round(start[1] + t * (end[1] - start[1]))
            z = round(start[2] + t * (end[2] - start[2]))
            pos = (x, y, z)
            if pos not in positions:
                positions.append(pos)
                
        return positions
        
    def _do_fill(self, pick_result: Optional[VoxelPickResult]):
        """Flood fill from clicked position (bounded)."""
        if not pick_result or not self.canvas:
            return
            
        start_pos = pick_result.adjacent_pos
        
        # Only fill if starting in empty space
        if start_pos in self.canvas.voxels:
            return
            
        # Bounded flood fill (max 100 blocks, within [-8, 8] range)
        filled = set()
        to_fill = [start_pos]
        max_blocks = 100
        bounds = 8
        
        while to_fill and len(filled) < max_blocks:
            pos = to_fill.pop(0)
            
            if pos in filled:
                continue
            if pos in self.canvas.voxels:
                continue
            if abs(pos[0]) > bounds or abs(pos[1]) > bounds or abs(pos[2]) > bounds:
                continue
                
            filled.add(pos)
            
            # Add neighbors (6-connected)
            for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                neighbor = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
                if neighbor not in filled and neighbor not in self.canvas.voxels:
                    to_fill.append(neighbor)
                    
        # Place all filled blocks
        for pos in filled:
            self._add_block(pos, self.selected_block_type, rebuild=False)
            
        # Rebuild mesh once at the end
        self.canvas.rebuild_mesh()
        self.picker.sync_with_canvas(self.canvas.voxels)
        
    def _do_erase(self, pick_result: Optional[VoxelPickResult]):
        """Erase a block."""
        if not pick_result:
            return
        self._remove_block(pick_result.hit_pos)
        
    def _do_place_entity(self, pick_result: Optional[VoxelPickResult]):
        """Place an entity marker."""
        if not pick_result or not self.markers:
            return
            
        # Place entity on top of clicked block
        pos = pick_result.hit_pos
        entity_pos = (pos[0], pos[1], pos[2] + 1)
        self.markers.add_marker(entity_pos, self.selected_entity_type)
        
    # --- Block Manipulation ---
    
    def _add_block(self, pos: Tuple[int, int, int], block_type: str, rebuild: bool = True):
        """Add a block at position with undo support."""
        if not self.canvas:
            return
        
        # Skip if block already exists at this position
        if pos in self.canvas.voxels:
            return
            
        # Capture state for undo closure
        captured_pos = pos
        captured_type = block_type
        
        def do_add():
            self.canvas.add_voxel_with_type(captured_pos, captured_type)
            
        def do_remove():
            self.canvas.remove_voxel(captured_pos)
            
        cmd = EditorCommand(
            execute=do_add,
            undo=do_remove,
            description=f"Place {block_type} at {pos}"
        )
        self.history.execute(cmd)
        self._mark_dirty()
        
        if rebuild:
            self.picker.sync_with_canvas(self.canvas.voxels)
            
    def _remove_block(self, pos: Tuple[int, int, int]):
        """Remove a block at position with undo support."""
        if not self.canvas:
            return
        
        # Skip if no block at this position
        if pos not in self.canvas.voxels:
            return
            
        # Capture existing block for undo
        captured_pos = pos
        captured_type = self.canvas.block_types.get(pos, "stone")
        captured_color = self.canvas.voxels.get(pos, (0.8, 0.8, 0.8, 1))
        
        def do_remove():
            self.canvas.remove_voxel(captured_pos)
            
        def do_restore():
            self.canvas.add_voxel_with_type(captured_pos, captured_type, captured_color)
            
        cmd = EditorCommand(
            execute=do_remove,
            undo=do_restore,
            description=f"Remove block at {pos}"
        )
        self.history.execute(cmd)
        self._mark_dirty()
        self.picker.sync_with_canvas(self.canvas.voxels)
        
    # --- Toolbar Actions ---
        
    def _on_save(self):
        """Save POI template."""
        logger.info("Saving POI...")
        try:
            template = POITemplate(
                name=self.properties.current_poi_data["name"],
                poi_type=self.properties.current_poi_data["type"],
                biome_affinity=[self.properties.current_poi_data["biome"]],
                blocks=self.canvas.to_poi_blocks(),
                entities=self.markers.to_poi_entities() if self.markers else []
            )
            template.calculate_bounds()
            
            filename = template.name.lower().replace(" ", "_")
            self.app.asset_manager.save_poi_template(template, filename)
            logger.info(f"Saved {filename}.mcp")
            self._mark_clean()
            self._show_toast(f"Saved: {filename}.mcp", "success")
            self.properties.refresh_templates()  # Update dropdown
        except Exception as e:
            logger.error(f"Save failed: {e}")
            self._show_toast(f"Save failed: {e}", "error")
            
    def _on_load(self):
        """Load POI template."""
        logger.info("Loading POI...")
        try:
            filename = self.properties.current_poi_data["name"].lower().replace(" ", "_")
            template = self.app.asset_manager.load_poi_template(filename)
            
            self.canvas.from_poi_blocks(template.blocks)
            if self.markers:
                self.markers.from_poi_entities(template.entities)
                
            self.picker.sync_with_canvas(self.canvas.voxels)
            self.current_template_name = template.name
            self.history.clear()  # Clear history on load
            logger.info(f"Loaded {template.name}")
            self._show_toast(f"Loaded: {template.name}", "success")
        except Exception as e:
            logger.error(f"Load failed: {e}")
            self._show_toast(f"Load failed: {e}", "error")
            
    def _on_clear(self):
        """Clear all user-placed blocks and entities, keeping base floor."""
        if self.canvas:
            self.canvas.clear()
            self._create_base_floor()
        if self.markers:
            self.markers.clear()
        if self.picker:
            self.picker.sync_with_canvas(self.canvas.voxels)
        self.history.clear()  # Clear history to prevent undo restoring cleared items
        self._show_toast("Canvas cleared", "info")
        
    def _create_base_floor(self):
        """Create the starter floor grid (not tracked in undo history)."""
        half = self.canvas.size // 2
        for x in range(-half, half + 1):
            for y in range(-half, half + 1):
                # Add directly to canvas, bypassing history
                self.canvas.add_voxel_with_type((x, y, 0), "grass")
            
    def _on_undo(self):
        """Undo last action."""
        if self.history.undo():
            self.picker.sync_with_canvas(self.canvas.voxels)
            desc = self.history.get_redo_description()
            logger.debug(f"Undid action (can redo: {desc})")
        else:
            logger.debug("Nothing to undo")
        
    def _on_redo(self):
        """Redo last undone action."""
        if self.history.redo():
            self.picker.sync_with_canvas(self.canvas.voxels)
            desc = self.history.get_undo_description()
            logger.debug(f"Redid action (can undo: {desc})")
        else:
            logger.debug("Nothing to redo")
            
    def _show_toast(self, message: str, toast_type: str = "info"):
        """Show a toast notification."""
        if not hasattr(self, '_toast') or self._toast is None:
            self._toast = ToastNotification(self.app.aspect2d)
        
        if toast_type == "success":
            self._toast.show_success(message)
        elif toast_type == "error":
            self._toast.show_error(message)
        else:
            self._toast.show_info(message)
            
    # --- Dirty State Tracking ---
    
    @property
    def is_dirty(self) -> bool:
        """Check if there are unsaved changes."""
        return self._dirty
        
    def _mark_dirty(self):
        """Mark workspace as having unsaved changes."""
        self._dirty = True
        
    def _mark_clean(self):
        """Mark workspace as saved/clean."""
        self._dirty = False
        
    # --- Template Browser Callbacks ---
    
    def _on_template_load_request(self, template_name: str):
        """Handle Load button from template browser."""
        if self._dirty:
            self._show_confirm_dialog(
                "You have unsaved changes. Load anyway?",
                on_yes=lambda: self._do_load_template(template_name)
            )
        else:
            self._do_load_template(template_name)
            
    def _do_load_template(self, template_name: str):
        """Actually load a template by name."""
        logger.info(f"Loading template: {template_name}")
        try:
            template = self.app.asset_manager.load_poi_template(template_name)
            
            self.canvas.from_poi_blocks(template.blocks)
            if self.markers:
                self.markers.from_poi_entities(template.entities)
                
            self.picker.sync_with_canvas(self.canvas.voxels)
            self.current_template_name = template.name
            self.history.clear()
            self._mark_clean()
            
            # Update property panel name
            self.properties.poi_name = template.name
            self.properties.name_entry.enterText(template.name)
            
            logger.info(f"Loaded {template.name}")
            self._show_toast(f"Loaded: {template.name}", "success")
        except Exception as e:
            logger.error(f"Load failed: {e}")
            self._show_toast(f"Load failed: {e}", "error")
            
    def _on_template_new_request(self):
        """Handle New button from template browser."""
        if self._dirty:
            self._show_confirm_dialog(
                "You have unsaved changes. Create new anyway?",
                on_yes=self._do_new_template
            )
        else:
            self._do_new_template()
            
    def _do_new_template(self):
        """Create a new empty template."""
        self._on_clear()
        self.properties.poi_name = "untitled_poi"
        self.properties.name_entry.enterText("untitled_poi")
        self._mark_clean()
        self._show_toast("New template created", "info")
        
    def _show_confirm_dialog(self, message: str, on_yes=None, on_no=None):
        """Show a confirmation dialog."""
        if not self._confirm_dialog:
            self._confirm_dialog = ConfirmationDialog(self.app.aspect2d)
        self._confirm_dialog.show(message, on_yes=on_yes, on_no=on_no)
