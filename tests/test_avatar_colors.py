"""
Tests for the AvatarColors ECS component.
"""
import unittest

from engine.components.avatar_colors import AvatarColors


class TestAvatarColors(unittest.TestCase):
    """Test AvatarColors component."""
    
    def test_component_creation(self):
        """Test creating AvatarColors with default values."""
        colors = AvatarColors()
        
        # Default body color is green
        self.assertEqual(colors.body_color, (0.2, 0.8, 0.2, 1.0))
        
        # No bone overrides initially
        self.assertEqual(len(colors.bone_colors), 0)
        
        # No temporary color
        self.assertIsNone(colors.temporary_color)
        self.assertEqual(colors.temp_timer, 0.0)
        
        # Starter colors unlocked by default
        self.assertEqual(len(colors.unlocked_colors), 8)
        self.assertIn("red", colors.unlocked_colors)
        self.assertIn("blue", colors.unlocked_colors)
    
    def test_body_color_update(self):
        """Test updating body color."""
        colors = AvatarColors()
        
        # Change to red
        colors.body_color = (1.0, 0.0, 0.0, 1.0)
        self.assertEqual(colors.body_color, (1.0, 0.0, 0.0, 1.0))
    
    def test_bone_color_override(self):
        """Test per-bone color overrides."""
        colors = AvatarColors()
        
        # Set head to blue
        colors.bone_colors["head"] = (0.0, 0.0, 1.0, 1.0)
        
        # Get effective color for head (should be blue)
        head_color = colors.get_effective_color("head")
        self.assertEqual(head_color, (0.0, 0.0, 1.0, 1.0))
        
        # Get effective color for chest (should be body color)
        chest_color = colors.get_effective_color("chest")
        self.assertEqual(chest_color, colors.body_color)
    
    def test_temporary_color(self):
        """Test temporary color override."""
        colors = AvatarColors()
        
        # Apply temporary pink color
        pink = (1.0, 0.75, 0.8, 1.0)
        colors.apply_temporary_color(pink, duration=60.0)
        
        self.assertEqual(colors.temporary_color, pink)
        self.assertEqual(colors.temp_timer, 60.0)
        
        # Temporary color overrides everything
        self.assertEqual(colors.get_effective_color("head"), pink)
        self.assertEqual(colors.get_effective_color("chest"), pink)
    
    def test_temporary_color_timer_update(self):
        """Test temporary color timer countdown."""
        colors = AvatarColors()
        colors.apply_temporary_color((1.0, 0.0, 0.0, 1.0), duration=5.0)
        
        # Update timer
        colors.update_temp_timer(2.0)
        self.assertEqual(colors.temp_timer, 3.0)
        
        # Update again
        colors.update_temp_timer(2.0)
        self.assertEqual(colors.temp_timer, 1.0)
        
        # Update past zero - should clear
        colors.update_temp_timer(2.0)
        self.assertIsNone(colors.temporary_color)
        self.assertEqual(colors.temp_timer, 0.0)
    
    def test_clear_temporary_color(self):
        """Test manually clearing temporary color."""
        colors = AvatarColors()
        colors.apply_temporary_color((1.0, 0.0, 0.0, 1.0), duration=60.0)
        
        colors.clear_temporary_color()
        
        self.assertIsNone(colors.temporary_color)
        self.assertEqual(colors.temp_timer, 0.0)
    
    def test_unlock_color(self):
        """Test unlocking new colors."""
        colors = AvatarColors()
        
        # Unlock crimson (not in starter set)
        result = colors.unlock_color("crimson")
        self.assertTrue(result)  # Newly unlocked
        self.assertIn("crimson", colors.unlocked_colors)
        
        # Try unlocking again
        result = colors.unlock_color("crimson")
        self.assertFalse(result)  # Already unlocked
    
    def test_has_color(self):
        """Test checking if color is unlocked."""
        colors = AvatarColors()
        
        # Starter colors should be unlocked
        self.assertTrue(colors.has_color("red"))
        self.assertTrue(colors.has_color("blue"))
        
        # Loot colors should not be unlocked initially
        self.assertFalse(colors.has_color("crimson"))
        
        # Unlock and check again
        colors.unlock_color("crimson")
        self.assertTrue(colors.has_color("crimson"))
    
    def test_effective_color_priority(self):
        """Test color priority: temporary > bone override > body color."""
        colors = AvatarColors()
        
        # Set body color to green
        colors.body_color = (0.0, 1.0, 0.0, 1.0)
        
        # Set head to blue
        colors.bone_colors["head"] = (0.0, 0.0, 1.0, 1.0)
        
        # Without temp color: head is blue, chest is green
        self.assertEqual(colors.get_effective_color("head"), (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(colors.get_effective_color("chest"), (0.0, 1.0, 0.0, 1.0))
        
        # Apply temporary red color
        colors.apply_temporary_color((1.0, 0.0, 0.0, 1.0), duration=60.0)
        
        # With temp color: everything is red
        self.assertEqual(colors.get_effective_color("head"), (1.0, 0.0, 0.0, 1.0))
        self.assertEqual(colors.get_effective_color("chest"), (1.0, 0.0, 0.0, 1.0))
        
        # Clear temp color
        colors.clear_temporary_color()
        
        # Back to original: head is blue, chest is green
        self.assertEqual(colors.get_effective_color("head"), (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(colors.get_effective_color("chest"), (0.0, 1.0, 0.0, 1.0))


if __name__ == "__main__":
    unittest.main()
