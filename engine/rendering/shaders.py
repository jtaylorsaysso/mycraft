"""Procedural shaders for rendering effects."""

from panda3d.core import Shader

SKY_SHADER = Shader.make(Shader.SL_GLSL,
    vertex="""
    #version 150
    uniform mat4 p3d_ModelViewProjectionMatrix;
    in vec4 p3d_Vertex;
    out float v_height;
    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        v_height = p3d_Vertex.z; // Use vertex height for gradient
    }
    """,
    fragment="""
    #version 150
    in float v_height;
    out vec4 fragColor;
    uniform vec3 horizon_color;
    uniform vec3 zenith_color;
    void main() {
        // Simple linear gradient based on height
        float t = clamp(v_height / 100.0, 0.0, 1.0);
        vec3 color = mix(horizon_color, zenith_color, t);
        fragColor = vec4(color, 1.0);
    }
    """
)

WATER_WOBBLE_SHADER = Shader.make(Shader.SL_GLSL,
    vertex="""
    #version 150
    uniform mat4 p3d_ModelViewProjectionMatrix;
    uniform float time;
    uniform float wobble_frequency;
    uniform float wobble_amplitude;
    
    in vec4 p3d_Vertex;
    in vec4 p3d_Color;
    in vec2 p3d_MultiTexCoord0;
    in vec3 block_id;  // Custom attribute: block world position for phase
    
    out vec4 v_color;
    out vec2 v_texcoord;
    out float v_depth;
    
    void main() {
        vec4 vertex = p3d_Vertex;
        
        // Per-block unique phase (prevents uniform wave pattern)
        float phase = block_id.x * 13.7 + block_id.y * 27.3 + block_id.z * 19.1;
        
        // Calculate block center Z (for determining top vertices)
        float block_center_z = floor(block_id.z) + 0.5;
        
        // Only wobble top vertices (z > block center)
        if (vertex.z > block_center_z) {
            float freq = wobble_frequency;
            float amp = wobble_amplitude;
            
            // Multi-frequency wobble for natural look
            vertex.x += sin(time * freq + phase) * amp;
            vertex.y += sin(time * freq * 1.3 + phase + 2.1) * amp;
            vertex.z += cos(time * freq * 0.8 + phase) * amp * 1.6;  // Stronger vertical
        }
        
        gl_Position = p3d_ModelViewProjectionMatrix * vertex;
        v_color = p3d_Color;
        v_texcoord = p3d_MultiTexCoord0;
        v_depth = block_id.z;  // Pass depth for color variation
    }
    """,
    fragment="""
    #version 150
    in vec4 v_color;
    in vec2 v_texcoord;
    in float v_depth;
    out vec4 fragColor;
    
    uniform float water_alpha;
    
    void main() {
        // Depth-based color darkening (10% darker per block depth)
        float depth_factor = 1.0 - (max(0.0, -v_depth) * 0.1);
        depth_factor = clamp(depth_factor, 0.3, 1.0);  // Don't go too dark
        
        vec4 final_color = v_color * depth_factor;
        final_color.a = water_alpha;  // Semi-transparent
        
        fragColor = final_color;
    }
    """
)
