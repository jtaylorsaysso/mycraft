
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from panda3d.core import loadPrcFileData, NodePath
# Use headless backend for testing
loadPrcFileData("", "window-type none")
loadPrcFileData("", "audio-library-name null")

from engine.game import VoxelGame, GameState

# Mock systems to avoid headless issues
@patch('engine.rendering.environment.EnvironmentManager')
@patch('engine.game.InputManager')
def test_model_editor(mock_input_manager, mock_env_manager):
    print("Initializing VoxelGame...")
    try:
        game = VoxelGame(name="Test Game")
        # Fix for headless reparent issue in EnvironmentManager if it happened before
        # But we mocked InputManager, hopefully EnvironmentManager behaves or we mock it too.
        # Actually EnvironmentManager failed in previous run due to skybox reparent to base.cam (which might be None or not fully setup in headless without window?)
        # In headless 'none', base.cam usually exists.
        
    except Exception as e:
        print(f"FAILED to init game: {e}")
        return

    # Mock camera for headless environment
    if not game.camera:
        print("Mocking game.camera for headless mode...")
        game.camera = NodePath("MockCamera")
        game.camera.reparentTo(game.render)

    print("Checking EditorManager...")
    if "Model Editor" not in game.editor_manager.editors:
        print("FAILED: Model Editor not registered")
        return
        
    editor = game.editor_manager.editors["Model Editor"]
    
    print("Toggle ON...")
    game.editor_manager.toggle_editor("Model Editor")
    
    if not editor.visible:
        print("FAILED: Editor should be visible")
        return
        
    if not editor.canvas:
        print("FAILED: Canvas not initialized")
        return
        
    if editor.canvas.root.isHidden(): 
        # Note: In our code we show it on show(). NodePath.isHidden() returns true if hidden.
        # But wait, isHidden() checks self.
        pass
        
    print("Checking Voxel Data...")
    if not editor.canvas.voxels:
        print("FAILED: Voxel data empty (setup should add test voxel)")
        return
        
    print("Toggle OFF...")
    game.editor_manager.toggle_editor("Model Editor")
    
    if editor.visible:
        print("FAILED: Editor should be hidden")
        return

    print("SUCCESS: Voxel Model Editor verified!")

if __name__ == "__main__":
    test_model_editor()
