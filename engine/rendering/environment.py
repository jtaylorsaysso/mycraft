"""Environment systems for Panda3D (Skybox, Fog, etc.)."""

from panda3d.core import (
    NodePath, CardMaker, LVector3f, Fog,
    ColorAttrib, TransparencyAttrib
)

class EnvironmentManager:
    """Manages skybox, fog, and global lighting settings."""
    
    def __init__(self, base):
        """Initialize environment manager.
        
        Args:
            base: ShowBase instance
        """
        self.base = base
        self.skybox = None
        self.fog = None
        
        # Default colors
        self.horizon_color = LVector3f(0.7, 0.8, 0.9)  # Light blue
        self.zenith_color = LVector3f(0.2, 0.4, 0.8)   # Deep blue
        self.fog_color = LVector3f(0.8, 0.8, 0.8)      # Light grey
        
        # Setup
        self.setup_fog()
        self.setup_skybox()
        
    def setup_fog(self):
        """Set up global distance fog."""
        self.fog = Fog("environment_fog")
        self.fog.setColor(self.fog_color.x, self.fog_color.y, self.fog_color.z)
        
        # Linear fog: start at 50, dense at 150
        # This helps hide chunk loading at the edges
        self.fog.setLinearRange(50, 150)
        
        self.base.render.setFog(self.fog)
        self.base.setBackgroundColor(self.fog_color.x, self.fog_color.y, self.fog_color.z)
        
    def setup_skybox(self):
        """Create a simple procedural gradient skybox."""
        # Create a large sphere for the sky
        from engine.rendering.shaders import SKY_SHADER
        
        # Create a sphere model procedurally or load a simple one
        # For now, we'll use a large Card as a simple background, 
        # but reparented to camera to always stay behind.
        cm = CardMaker('sky')
        cm.setFrame(-1, 1, -1, 1)
        self.skybox = self.base.render.attachNewNode(cm.generate())
        self.skybox.setScale(500) # Distant
        self.skybox.setBin('background', 0)
        self.skybox.setDepthWrite(False)
        self.skybox.setLightOff()
        
        self.skybox.setShader(SKY_SHADER)
        self.skybox.setShaderInput("horizon_color", self.horizon_color)
        self.skybox.setShaderInput("zenith_color", self.zenith_color)
        
        # Track camera Pos but not move with it (stay centered)
        # Actually, let's reparent to camera and set distance
        self.skybox.reparentTo(self.base.cam)
        self.skybox.setPos(0, 500, 0)
        self.skybox.setHpr(0, 90, 0) # Face camera
    
    def set_fog_range(self, start: float, end: float):
        """Update fog distance."""
        if self.fog:
            self.fog.setLinearRange(start, end)
            
    def set_colors(self, horizon: LVector3f, zenith: LVector3f, fog: LVector3f):
        """Update environment colors."""
        self.horizon_color = horizon
        self.zenith_color = zenith
        self.fog_color = fog
        
        if self.fog:
            self.fog.setColor(fog.x, fog.y, fog.z)
        self.base.setBackgroundColor(fog.x, fog.y, fog.z)
