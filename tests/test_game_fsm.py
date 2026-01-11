"""
Unit tests for the hierarchical game state machine.
"""

import unittest
from unittest.mock import MagicMock, patch

# FSM raises this exception for invalid transitions
from direct.fsm.FSM import RequestDenied

# Force real Panda3D FSM import (not mocked)
from panda3d.core import loadPrcFileData
loadPrcFileData("", "window-type none")
loadPrcFileData("", "audio-library-name null")


class TestGameFSM(unittest.TestCase):
    """Tests for GameFSM state transitions."""
    
    def setUp(self):
        """Create mock game for testing."""
        self.mock_game = MagicMock()
        self.mock_game.input_manager = MagicMock()
        
        from engine.core.game_fsm import GameFSM
        self.fsm = GameFSM(self.mock_game)
    
    def test_initial_state_is_off(self):
        """FSM starts in 'Off' state before any request."""
        self.assertEqual(self.fsm.state, 'Off')
    
    def test_request_playing(self):
        """Can transition to Playing state."""
        self.fsm.request('Playing')
        self.assertEqual(self.fsm.state, 'Playing')
    
    def test_playing_locks_cursor(self):
        """Entering Playing state locks cursor."""
        self.fsm.request('Playing')
        self.mock_game.input_manager.lock_mouse.assert_called()
    
    def test_request_paused_from_playing(self):
        """Can transition from Playing to Paused."""
        self.fsm.request('Playing')
        self.fsm.request('Paused')
        self.assertEqual(self.fsm.state, 'Paused')
    
    def test_paused_unlocks_cursor(self):
        """Entering Paused state unlocks cursor."""
        self.fsm.request('Playing')
        self.mock_game.input_manager.reset_mock()
        self.fsm.request('Paused')
        self.mock_game.input_manager.unlock_mouse.assert_called()
    
    def test_cannot_pause_from_main_menu(self):
        """Cannot go directly from MainMenu to Paused - should raise."""
        self.fsm.request('MainMenu')
        with self.assertRaises(RequestDenied):
            self.fsm.request('Paused')
        # Should remain in MainMenu since transition was rejected
        self.assertEqual(self.fsm.state, 'MainMenu')
    
    def test_toggle_pause(self):
        """Toggling pause goes Playing -> Paused -> Playing."""
        self.fsm.request('Playing')
        self.assertEqual(self.fsm.state, 'Playing')
        
        self.fsm.request('Paused')
        self.assertEqual(self.fsm.state, 'Paused')
        
        self.fsm.request('Playing')
        self.assertEqual(self.fsm.state, 'Playing')


class TestPlayingFSM(unittest.TestCase):
    """Tests for PlayingFSM sub-state transitions."""
    
    def setUp(self):
        """Create mock game for testing."""
        self.mock_game = MagicMock()
        self.mock_game.input_manager = MagicMock()
        
        from engine.core.game_fsm import PlayingFSM
        self.fsm = PlayingFSM(self.mock_game)
    
    def test_initial_state_is_off(self):
        """FSM starts in 'Off' state."""
        self.assertEqual(self.fsm.state, 'Off')
    
    def test_request_exploring(self):
        """Can transition to Exploring state."""
        self.fsm.request('Exploring')
        self.assertEqual(self.fsm.state, 'Exploring')
    
    def test_exploring_to_inventory(self):
        """Can transition from Exploring to InInventory."""
        self.fsm.request('Exploring')
        self.fsm.request('InInventory')
        self.assertEqual(self.fsm.state, 'InInventory')
    
    def test_inventory_blocks_input(self):
        """Entering InInventory blocks input."""
        self.fsm.request('Exploring')
        self.fsm.request('InInventory')
        self.mock_game.input_manager.block_input.assert_called_with("inventory")
    
    def test_exit_inventory_unblocks_input(self):
        """Exiting InInventory unblocks input."""
        self.fsm.request('Exploring')
        self.fsm.request('InInventory')
        self.mock_game.input_manager.reset_mock()
        self.fsm.request('Exploring')
        self.mock_game.input_manager.unblock_input.assert_called_with("inventory")
    
    def test_cannot_go_directly_between_substates(self):
        """Cannot transition directly between InDialogue and InInventory."""
        self.fsm.request('Exploring')
        self.fsm.request('InDialogue')
        self.assertEqual(self.fsm.state, 'InDialogue')
        
        # Try to go directly to InInventory (should fail, must go through Exploring)
        with self.assertRaises(RequestDenied):
            self.fsm.request('InInventory')
        # FSM should remain in InDialogue
        self.assertEqual(self.fsm.state, 'InDialogue')


if __name__ == '__main__':
    unittest.main()
