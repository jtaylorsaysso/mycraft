
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from panda3d.core import loadPrcFileData
# Use headless backend for testing
loadPrcFileData("", "window-type none")
loadPrcFileData("", "audio-library-name null")

from engine.game import VoxelGame
from engine.ui.animation_editor import AnimationEditorWindow

# Mock InputManager to avoid headless issues
from unittest.mock import patch
@patch('engine.game.InputManager')
def test_editor_architecture(mock_input_manager):
    print("Initializing VoxelGame...")
    try:
        game = VoxelGame(name="Test Game")
    except Exception as e:
        print(f"FAILED to init game: {e}")
        import traceback
        traceback.print_exc()
        return

    print("Checking EditorManager existence...")
    if not hasattr(game, 'editor_manager'):
        print("FAILED: game.editor_manager missing")
        return
        
    print("Checking registered editors...")
    if "Animation Editor" not in game.editor_manager.editors:
        print("FAILED: Animation Editor not registered")
        return
        
    print(f"Initial Game State: {game.game_state}")
    
    print("Toggling Animation Editor ON...")
    game.editor_manager.toggle_editor("Animation Editor")
    
    # Check visibility
    editor = game.editor_manager.editors["Animation Editor"]
    print(f"Editor Visible: {editor.visible}")
    if not editor.visible:
        print("FAILED: Editor should be visible")
        return
        
    # Check Game State (Should be Paused)
    print(f"Game State: {game.game_state}")
    if game.game_state != 'Paused':
        print(f"FAILED: Game state should be Paused, is {game.game_state}")
        return
        
    print("Toggling Animation Editor OFF...")
    game.editor_manager.toggle_editor("Animation Editor")
    
    print(f"Editor Visible: {editor.visible}")
    if editor.visible:
        print("FAILED: Editor should be hidden")
        return
        
    print(f"Game State: {game.game_state}")
    if game.game_state != 'Playing':
        print(f"FAILED: Game state should be Playing, is {game.game_state}")
        return

    print("SUCCESS: Editor architecture verification passed!")

if __name__ == "__main__":
    test_editor_architecture() # patch decorator handles the arg
