"""
Tests for the ColorPalette system.
"""
import unittest
import random

from engine.color.palette import ColorSwatch, ColorPalette


class TestColorSwatch(unittest.TestCase):
    """Test ColorSwatch dataclass."""
    
    def test_valid_color_creation(self):
        """Test creating a valid color swatch."""
        swatch = ColorSwatch("Red", (1.0, 0.0, 0.0, 1.0), "common")
        self.assertEqual(swatch.name, "Red")
        self.assertEqual(swatch.rgba, (1.0, 0.0, 0.0, 1.0))
        self.assertEqual(swatch.rarity, "common")
    
    def test_invalid_rgba_values_raise_error(self):
        """Test that invalid RGBA values raise ValueError."""
        # RGBA values must be in [0.0, 1.0]
        with self.assertRaises(ValueError):
            ColorSwatch("Invalid", (1.5, 0.0, 0.0, 1.0))  # R > 1.0
        
        with self.assertRaises(ValueError):
            ColorSwatch("Invalid", (0.0, -0.1, 0.0, 1.0))  # G < 0.0
    
    def test_default_rarity(self):
        """Test that rarity defaults to 'common'."""
        swatch = ColorSwatch("Blue", (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(swatch.rarity, "common")


class TestColorPalette(unittest.TestCase):
    """Test ColorPalette registry."""
    
    def test_starter_colors_exist(self):
        """Test that all 8 starter colors are defined."""
        expected_starters = ["red", "blue", "yellow", "green", "orange", "purple", "white", "black"]
        
        for color_name in expected_starters:
            self.assertIn(color_name, ColorPalette.STARTER_COLORS)
            swatch = ColorPalette.STARTER_COLORS[color_name]
            self.assertIsInstance(swatch, ColorSwatch)
    
    def test_loot_colors_exist(self):
        """Test that loot colors are defined."""
        # At least 12 loot colors per spec
        self.assertGreaterEqual(len(ColorPalette.LOOT_COLORS), 12)
        
        # Verify some expected loot colors
        expected_loot = ["crimson", "navy", "gold", "silver", "forest", "coral", "teal"]
        for color_name in expected_loot:
            self.assertIn(color_name, ColorPalette.LOOT_COLORS)
    
    def test_color_rgba_values_valid(self):
        """Test that all colors have valid RGBA values."""
        all_colors = ColorPalette.get_all_colors()
        
        for name, swatch in all_colors.items():
            r, g, b, a = swatch.rgba
            self.assertGreaterEqual(r, 0.0, f"{name} red channel < 0.0")
            self.assertLessEqual(r, 1.0, f"{name} red channel > 1.0")
            self.assertGreaterEqual(g, 0.0, f"{name} green channel < 0.0")
            self.assertLessEqual(g, 1.0, f"{name} green channel > 1.0")
            self.assertGreaterEqual(b, 0.0, f"{name} blue channel < 0.0")
            self.assertLessEqual(b, 1.0, f"{name} blue channel > 1.0")
            self.assertGreaterEqual(a, 0.0, f"{name} alpha channel < 0.0")
            self.assertLessEqual(a, 1.0, f"{name} alpha channel > 1.0")
    
    def test_get_color_case_insensitive(self):
        """Test that get_color is case-insensitive."""
        red_lower = ColorPalette.get_color("red")
        red_upper = ColorPalette.get_color("RED")
        red_mixed = ColorPalette.get_color("Red")
        
        self.assertIsNotNone(red_lower)
        self.assertEqual(red_lower, red_upper)
        self.assertEqual(red_lower, red_mixed)
    
    def test_get_color_returns_none_for_invalid(self):
        """Test that get_color returns None for invalid color names."""
        result = ColorPalette.get_color("nonexistent_color")
        self.assertIsNone(result)
    
    def test_get_random_loot_color(self):
        """Test random loot color selection with seed."""
        rng = random.Random(42)
        
        # Get 10 random colors
        colors = [ColorPalette.get_random_loot_color(rng) for _ in range(10)]
        
        # All should be ColorSwatch instances
        for color in colors:
            self.assertIsInstance(color, ColorSwatch)
        
        # All should be from loot palette
        for color in colors:
            self.assertIn(color.name.lower(), [c.lower() for c in ColorPalette.get_loot_color_names()])
    
    def test_get_random_loot_color_deterministic(self):
        """Test that random color selection is deterministic with same seed."""
        rng1 = random.Random(123)
        rng2 = random.Random(123)
        
        color1 = ColorPalette.get_random_loot_color(rng1)
        color2 = ColorPalette.get_random_loot_color(rng2)
        
        self.assertEqual(color1.name, color2.name)
    
    def test_get_all_colors(self):
        """Test that get_all_colors returns combined palette."""
        all_colors = ColorPalette.get_all_colors()
        
        # Should contain all starter colors
        for name in ColorPalette.STARTER_COLORS.keys():
            self.assertIn(name, all_colors)
        
        # Should contain all loot colors
        for name in ColorPalette.LOOT_COLORS.keys():
            self.assertIn(name, all_colors)
        
        # Total count should be starter + loot
        expected_count = len(ColorPalette.STARTER_COLORS) + len(ColorPalette.LOOT_COLORS)
        self.assertEqual(len(all_colors), expected_count)
    
    def test_get_starter_color_names(self):
        """Test getting list of starter color names."""
        names = ColorPalette.get_starter_color_names()
        self.assertEqual(len(names), 8)
        self.assertIn("red", names)
        self.assertIn("blue", names)
    
    def test_get_loot_color_names(self):
        """Test getting list of loot color names."""
        names = ColorPalette.get_loot_color_names()
        self.assertGreaterEqual(len(names), 12)
        self.assertIn("crimson", names)
        self.assertIn("gold", names)


if __name__ == "__main__":
    unittest.main()
