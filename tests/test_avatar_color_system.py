"""
Tests for AvatarColorSystem.
"""
import unittest
from unittest.mock import MagicMock, Mock

from engine.ecs.world import World
from engine.ecs.events import EventBus
from engine.systems.avatar_color_system import AvatarColorSystem
from engine.components.avatar_colors import AvatarColors


class TestAvatarColorSystem(unittest.TestCase):
    """Test AvatarColorSystem functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.world = World()
        self.event_bus = EventBus()
        self.game = MagicMock()
        
        self.system = AvatarColorSystem(self.world, self.event_bus, self.game)
    
    def test_system_initialization(self):
        """Test system initializes correctly."""
        self.assertEqual(self.system.world, self.world)
        self.assertEqual(self.system.event_bus, self.event_bus)
        self.assertEqual(self.system.game, self.game)
    
    def test_update_with_no_player(self):
        """Test update handles missing player gracefully."""
        # Should not crash when no player exists
        self.system.update(0.016)
    
    def test_update_with_player_no_colors(self):
        """Test update handles player without AvatarColors component."""
        # Create player entity
        player = self.world.create_entity()
        self.world.register_tag(player, "player")
        
        # Should not crash when player has no AvatarColors
        self.system.update(0.016)
    
    def test_temp_timer_updates(self):
        """Test that temporary color timer counts down."""
        # Create player with AvatarColors
        player = self.world.create_entity()
        self.world.register_tag(player, "player")
        
        colors = AvatarColors()
        colors.apply_temporary_color((1.0, 0.0, 0.0, 1.0), duration=5.0)
        self.world.add_component(player, colors)
        
        # Initial timer
        self.assertEqual(colors.temp_timer, 5.0)
        
        # Update system (no avatar, but timer should still update)
        self.system.update(1.0)
        
        # Timer should have decreased
        self.assertEqual(colors.temp_timer, 4.0)
        
        # Update again
        self.system.update(2.0)
        self.assertEqual(colors.temp_timer, 2.0)
        
        # Update past zero
        self.system.update(3.0)
        self.assertIsNone(colors.temporary_color)
        self.assertEqual(colors.temp_timer, 0.0)
    
    def test_get_player_avatar_no_system(self):
        """Test _get_player_avatar returns None when PlayerControlSystem missing."""
        # Mock world.get_system_by_type to return None
        self.world.get_system_by_type = Mock(return_value=None)
        
        avatar = self.system._get_player_avatar()
        self.assertIsNone(avatar)
    
    def test_get_player_avatar_no_animation_mechanic(self):
        """Test _get_player_avatar returns None when AnimationMechanic missing."""
        # Mock PlayerControlSystem with no AnimationMechanic
        mock_player_system = MagicMock()
        mock_player_system.mechanics = []
        
        self.world.get_system_by_type = Mock(return_value=mock_player_system)
        
        avatar = self.system._get_player_avatar()
        self.assertIsNone(avatar)
    
    def test_get_player_avatar_success(self):
        """Test _get_player_avatar returns avatar when available."""
        # Mock AnimationMechanic with avatar
        mock_avatar = MagicMock()
        mock_animation_mechanic = MagicMock()
        mock_animation_mechanic.__class__.__name__ = "AnimationMechanic"
        mock_animation_mechanic.avatar = mock_avatar
        
        # Mock PlayerControlSystem
        mock_player_system = MagicMock()
        mock_player_system.mechanics = [mock_animation_mechanic]
        
        self.world.get_system_by_type = Mock(return_value=mock_player_system)
        
        avatar = self.system._get_player_avatar()
        self.assertEqual(avatar, mock_avatar)


if __name__ == "__main__":
    unittest.main()
