"""Chest inventory UI overlay."""

from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from panda3d.core import TextNode


class ChestInventoryOverlay:
    """UI panel for viewing and taking items from chests."""
    
    def __init__(self, base, world, loot_system, on_close=None):
        """Initialize chest inventory overlay.
        
        Args:
            base: ShowBase instance
            world: ECS World
            loot_system: LootSystem instance for spawning pickups
            on_close: Callback when chest is closed
        """
        self.base = base
        self.world = world
        self.loot_system = loot_system
        self.on_close = on_close
        self.visible = False
        self.current_chest_entity = None
        self.item_buttons = []
        
        # Semi-transparent background
        self.frame = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-1.2, 1.2, -1, 1),
            pos=(0, 0, 0),
            parent=base.aspect2d,
            relief=DGG.FLAT
        )
        
        # Title
        self.title_label = DirectLabel(
            text="Chest",
            scale=0.12,
            pos=(0, 0, 0.8),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            parent=self.frame
        )
        
        # Item grid container (will be populated dynamically)
        self.item_grid_frame = DirectFrame(
            frameColor=(0.2, 0.2, 0.2, 0.6),
            frameSize=(-1, 1, -0.6, 0.6),
            pos=(0, 0, 0.1),
            parent=self.frame,
            relief=DGG.SUNKEN
        )
        
        # Take All button
        self.take_all_button = DirectButton(
            text="Take All",
            scale=0.08,
            pos=(-0.4, 0, -0.8),
            frameColor=(0.2, 0.8, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_take_all,
            parent=self.frame,
            relief=DGG.RAISED
        )
        
        # Close button
        self.close_button = DirectButton(
            text="Close (ESC)",
            scale=0.08,
            pos=(0.4, 0, -0.8),
            frameColor=(0.8, 0.2, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_close_clicked,
            parent=self.frame,
            relief=DGG.RAISED
        )
        
        self.frame.hide()
    
    def open(self, chest_entity):
        """Open the chest UI for a specific chest entity.
        
        Args:
            chest_entity: Entity ID of the chest to open
        """
        from engine.components.chest import ChestComponent
        from engine.components.core import Transform
        
        chest = self.world.get_component(chest_entity, ChestComponent)
        if not chest or chest.is_open:
            return
        
        self.current_chest_entity = chest_entity
        self.visible = True
        
        # Update title with POI type if available
        if chest.poi_type:
            self.title_label['text'] = f"Chest ({chest.poi_type})"
        
        # Clear previous item buttons
        for button in self.item_buttons:
            button.destroy()
        self.item_buttons.clear()
        
        # Create item buttons in a grid
        items = chest.items
        if not items:
            # Empty chest
            empty_label = DirectLabel(
                text="Empty",
                scale=0.1,
                pos=(0, 0, 0),
                text_fg=(0.7, 0.7, 0.7, 1),
                frameColor=(0, 0, 0, 0),
                parent=self.item_grid_frame
            )
            self.item_buttons.append(empty_label)
        else:
            # Layout items in a grid (3 columns)
            cols = 3
            rows = (len(items) + cols - 1) // cols
            
            for i, item in enumerate(items):
                row = i // cols
                col = i % cols
                
                # Calculate position
                x = -0.6 + col * 0.6
                y = 0.4 - row * 0.3
                
                # Item label
                item_label = DirectLabel(
                    text=item.replace("_", " ").title(),
                    scale=0.06,
                    pos=(x, 0, y + 0.08),
                    text_fg=(1, 1, 1, 1),
                    frameColor=(0, 0, 0, 0),
                    parent=self.item_grid_frame
                )
                self.item_buttons.append(item_label)
                
                # Take button
                take_button = DirectButton(
                    text="Take",
                    scale=0.05,
                    pos=(x, 0, y - 0.05),
                    frameColor=(0.3, 0.6, 1.0, 1),
                    text_fg=(1, 1, 1, 1),
                    command=lambda idx=i: self._on_take_item(idx),
                    parent=self.item_grid_frame,
                    relief=DGG.RAISED
                )
                self.item_buttons.append(take_button)
        
        self.frame.show()
    
    def _on_take_item(self, item_index):
        """Handle taking a single item."""
        from engine.components.chest import ChestComponent
        from engine.components.core import Transform
        
        chest = self.world.get_component(self.current_chest_entity, ChestComponent)
        transform = self.world.get_component(self.current_chest_entity, Transform)
        
        if not chest or item_index >= len(chest.items):
            return
        
        # Get item and remove from chest
        item = chest.items.pop(item_index)
        
        # Spawn pickup at chest location
        self._spawn_item_pickup(item, transform.position)
        
        # If chest is now empty, mark as open and close UI
        if not chest.items:
            chest.is_open = True
            self.close()
        else:
            # Refresh UI to show remaining items
            self.open(self.current_chest_entity)
    
    def _on_take_all(self):
        """Handle taking all items."""
        from engine.components.chest import ChestComponent
        from engine.components.core import Transform
        
        chest = self.world.get_component(self.current_chest_entity, ChestComponent)
        transform = self.world.get_component(self.current_chest_entity, Transform)
        
        if not chest:
            return
        
        # Spawn all items as pickups
        for item in chest.items:
            self._spawn_item_pickup(item, transform.position)
        
        # Clear chest and mark as open
        chest.items.clear()
        chest.is_open = True
        
        self.close()
    
    def _spawn_item_pickup(self, item_id, position):
        """Spawn a pickup entity for an item.
        
        Args:
            item_id: Item identifier (e.g., "sword_iron", "red")
            position: LVector3f position to spawn at
        """
        # Check if it's a color item
        from engine.color.palette import ColorPalette
        
        if ColorPalette.get_color(item_id):
            # It's a color swatch
            self.loot_system.spawn_color_swatch(item_id, position)
        else:
            # For now, treat other items as color swatches too (placeholder)
            # In the future, this would spawn different pickup types
            # For now, just spawn a random color as placeholder
            import random
            colors = ["red", "blue", "green", "yellow", "purple"]
            self.loot_system.spawn_color_swatch(random.choice(colors), position)
    
    def _on_close_clicked(self):
        """Handle close button click."""
        self.close()
    
    def close(self):
        """Close the chest UI."""
        if self.current_chest_entity:
            from engine.components.chest import ChestComponent
            chest = self.world.get_component(self.current_chest_entity, ChestComponent)
            if chest and not chest.items:
                chest.is_open = True
        
        self.visible = False
        self.current_chest_entity = None
        self.frame.hide()
        
        if self.on_close:
            self.on_close()
    
    def cleanup(self):
        """Clean up the overlay."""
        for button in self.item_buttons:
            button.destroy()
        self.item_buttons.clear()
        self.frame.destroy()
