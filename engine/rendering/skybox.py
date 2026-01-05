"""Procedural Skybox."""

from panda3d.core import NodePath, Loader, Shader, Texture, CardMaker, TransparencyAttrib
from direct.task import Task

class Skybox:
    """Procedural gradient skybox."""
    
    def __init__(self, render: NodePath, loader: Loader):
        self.render = render
        self.root = render.attachNewNode("skybox_root")
        
        # Create a sphere (or inverted sphere) for the sky
        # Using a simple model if available, or generating one
        # For now, let's use a simple loaded model or a card? 
        # A sphere is best. Panda usually has 'models/misc/sphere' but we might not have it in path.
        # We'll use a inverted cube (skybox) or just a background quad if simple.
        # Let's try to load a sphere primitive or use a card for gradient background (2D).
        # Actually, 2D background is easiest for gradient.
        
        # 1. Create a full-screen quad (behind everything)
        cm = CardMaker('skybox_quad')
        cm.setFrame(-1, 1, -1, 1) # Full screen normalized coords? 
        # No, for 3D skybox we usually use a large sphere.
        
        # Let's use the 'box' approach: inverted cube is standard.
        # But we want a gradient.
        
        # Alternative: Set background color of window + heavy fog?
        # User requested "Skybox/Atmosphere".
        
        # Let's try creating a sphere procedurally if we don't have a model.
        # Or checking if we have a default sphere.
        try:
            self.sky_model = loader.loadModel("models/misc/sphere")
        except:
            # Fallback: just rely on clear color if model missing (which it likely is in this env)
            # Or generate a card in the background.
            # Using Render2D for background?
            # Let's use a simpler approach: A background card parented to camera.
            pass
            
        if not hasattr(self, 'sky_model') or not self.sky_model:
            # Create a simple Card for gradient
            cm = CardMaker('sky_gradient')
            cm.setFrameFullscreenQuad()
            self.sky_model = NodePath(cm.generate())
            # Parent to render2d (GUI layer) but at back? 
            # Or camera?
            # If we parent to base.cam2d, it's covering everything.
            # Usually we use base.setBackgroundColor for simple gradient.
            
            # Since we want a gradient, maybe just setting a nice background color is "Step 1".
            # Currently it's void (black/grey).
            pass

        # Let's implement a proper "Atmosphere" class that sets the clear color 
        # and maybe adds some fog.
        
    def setup_simple_atmosphere(self, base):
        """Setup basic blue sky and fog."""
        # Sky Blue
        base.setBackgroundColor(0.53, 0.81, 0.92) # Sky blue
        
        # Fog
        from panda3d.core import Fog
        myFog = Fog("SkyFog")
        myFog.setColor(0.53, 0.81, 0.92)
        myFog.setExpDensity(0.02) # Start fog closer
        base.render.setFog(myFog)
        
        print("✅ Skybox: Simple atmosphere enabled (Blue Sky + Fog)")

    def cleanup(self):
        if self.root:
            self.root.removeNode()
