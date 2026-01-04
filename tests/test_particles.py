"""Tests for VoxelParticleSystem."""
import unittest
from unittest.mock import MagicMock, patch

# Stub classes for Panda3D types to allow math operations
class StubVec3:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = float(x), float(y), float(z)
    def __add__(self, other):
        return StubVec3(self.x + other.x, self.y + other.y, self.z + other.z)
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return StubVec3(self.x * other, self.y * other, self.z * other)
        return StubVec3(self.x * other.x, self.y * other.y, self.z * other.z)

class StubVec4:
    def __init__(self, x=0, y=0, z=0, w=0):
        self.x, self.y, self.z, self.w = float(x), float(y), float(z), float(w)

class StubNodePath:
    def __init__(self, name="mock"):
        self.name = name
        self.visible = True
        self.pos = StubVec3()
        self.scale = 1.0
        self.color_scale = StubVec4(1, 1, 1, 1)
        
    def attachNewNode(self, node):
        return StubNodePath("child")
        
    def hide(self): self.visible = False
    def show(self): self.visible = True
    def setPos(self, pos): self.pos = pos
    def setScale(self, scale): self.scale = scale
    def setTransparency(self, mode): pass
    def setBillboardPointEye(self): pass
    def setColorScale(self, color): self.color_scale = color
    
    # CardMaker.generate returns a PandaNode, we mock it passing a string or whatever
    def generate(self): return "geom"

@patch('engine.animation.particles.LVector3f', StubVec3)
@patch('engine.animation.particles.LVector4f', StubVec4)
@patch('engine.animation.particles.NodePath', StubNodePath)
@patch('engine.animation.particles.CardMaker', MagicMock())
@patch('engine.animation.particles.TransparencyAttrib', MagicMock())
class TestParticleSystem(unittest.TestCase):
    def test_emit_particles(self):
        """Particles should emit and activate."""
        from engine.animation.particles import VoxelParticleSystem
        
        render = StubNodePath("render")
        ps = VoxelParticleSystem(render, max_particles=10)
        
        # Override with StubNodePaths (although __init__ should create them now via StubNodePath)
        # Because we mocked NodePath globally in the module, ps.__init__ uses StubNodePath!
        # AND we mocked CardMaker to return a MagicMock, which generate() returns a string/mock.
        # render.attachNewNode returns StubNodePath.
        # So ps.particle_nodes should be populated with StubNodePaths.
        
        ps.emit(
            position=StubVec3(0, 0, 0),
            velocity=StubVec3(0, 0, 1),
            count=5
        )
        
        self.assertEqual(ps.active_count, 5)
        self.assertIsNotNone(ps.particles[0])
        self.assertTrue(ps.particle_nodes[0].visible)
    
    def test_particle_lifetime(self):
        """Particles should die after lifetime."""
        from engine.animation.particles import VoxelParticleSystem
        
        render = StubNodePath("render")
        ps = VoxelParticleSystem(render, max_particles=10)
        
        ps.emit(
            position=StubVec3(0, 0, 0),
            velocity=StubVec3(0, 0, 0),
            lifetime=0.5,
            count=1
        )
        
        # Update past lifetime
        ps.update(0.6)
        
        self.assertEqual(ps.active_count, 0)
        self.assertFalse(ps.particle_nodes[0].visible)
        
    def test_alpha_fading(self):
        """Particles should fade out over lifetime."""
        from engine.animation.particles import VoxelParticleSystem
        
        render = StubNodePath("render")
        ps = VoxelParticleSystem(render, max_particles=10)
        
        ps.emit(
             position=StubVec3(0, 0, 0),
             velocity=StubVec3(0, 0, 0),
             color=StubVec4(1, 1, 1, 1),
             lifetime=1.0,
             count=1
        )
        
        # Update halfway
        ps.update(0.5)
        
        # Alpha should be around 0.5
        # 1.0 - (0.5 / 1.0) = 0.5
        current_alpha = ps.particle_nodes[0].color_scale.w
        self.assertAlmostEqual(current_alpha, 0.5, places=2)
