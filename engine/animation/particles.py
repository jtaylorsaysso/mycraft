"""Voxel-based particle system for effects."""

from dataclasses import dataclass
from typing import List, Optional
from panda3d.core import NodePath, GeomNode, LVector3f, LVector4f
import random


@dataclass
class VoxelParticle:
    """Single voxel particle."""
    position: LVector3f
    velocity: LVector3f
    color: LVector4f
    size: float
    lifetime: float
    age: float = 0.0
    gravity: float = -9.8
    

class VoxelParticleSystem:
    """Particle system using tiny voxel cubes.
    
    Efficient pooled particle system for impacts, magic effects, etc.
    """
    
    def __init__(self, render: NodePath, max_particles: int = 1000):
        """Initialize particle system.
        
        Args:
            render: Panda3D render node
            max_particles: Maximum number of particles
        """
        self.render = render
        self.max_particles = max_particles
        self.particles: List[Optional[VoxelParticle]] = [None] * max_particles
        self.particle_nodes: List[Optional[NodePath]] = [None] * max_particles
        self.active_count = 0
        
        # Pre-create particle nodes (pooling)
        for i in range(max_particles):
            # TODO: Create actual voxel cube geometry
            # For now, placeholder
            node = render.attachNewNode(f'particle_{i}')
            node.hide()
            self.particle_nodes[i] = node
    
    def emit(
        self,
        position: LVector3f,
        velocity: LVector3f,
        color: LVector4f = LVector4f(1, 1, 1, 1),
        size: float = 0.1,
        lifetime: float = 1.0,
        count: int = 1,
        spread: float = 0.5
    ):
        """Emit particles.
        
        Args:
            position: Emission position
            velocity: Base velocity
            color: Particle color
            size: Particle size
            lifetime: Particle lifetime in seconds
            count: Number of particles to emit
            spread: Random velocity spread
        """
        for _ in range(count):
            # Find free particle slot
            for i in range(self.max_particles):
                if self.particles[i] is None:
                    # Add random spread to velocity
                    rand_vel = LVector3f(
                        random.uniform(-spread, spread),
                        random.uniform(-spread, spread),
                        random.uniform(-spread, spread)
                    )
                    
                    particle = VoxelParticle(
                        position=position,
                        velocity=velocity + rand_vel,
                        color=color,
                        size=size,
                        lifetime=lifetime
                    )
                    
                    self.particles[i] = particle
                    self.particle_nodes[i].setPos(position)
                    self.particle_nodes[i].setScale(size)
                    self.particle_nodes[i].show()
                    self.active_count += 1
                    break
    
    def update(self, dt: float):
        """Update all particles.
        
        Args:
            dt: Delta time
        """
        for i in range(self.max_particles):
            particle = self.particles[i]
            if particle is None:
                continue
            
            # Update particle
            particle.age += dt
            
            # Check if dead
            if particle.age >= particle.lifetime:
                self.particles[i] = None
                self.particle_nodes[i].hide()
                self.active_count -= 1
                continue
            
            # Apply physics
            particle.velocity.z += particle.gravity * dt
            particle.position += particle.velocity * dt
            
            # Update node
            self.particle_nodes[i].setPos(particle.position)
            
            # Fade out based on lifetime
            alpha = 1.0 - (particle.age / particle.lifetime)
            # TODO: Apply alpha to particle material
    
    def clear(self):
        """Clear all particles."""
        for i in range(self.max_particles):
            if self.particles[i] is not None:
                self.particles[i] = None
                self.particle_nodes[i].hide()
        self.active_count = 0


def create_impact_effect(
    particle_system: VoxelParticleSystem,
    position: LVector3f,
    normal: LVector3f,
    color: LVector4f = LVector4f(0.8, 0.8, 0.8, 1.0)
):
    """Create impact particle effect.
    
    Args:
        particle_system: Particle system to emit from
        position: Impact position
        normal: Surface normal
        color: Particle color
    """
    # Emit particles in hemisphere around normal
    base_velocity = normal * 2.0
    particle_system.emit(
        position=position,
        velocity=base_velocity,
        color=color,
        size=0.05,
        lifetime=0.5,
        count=10,
        spread=1.5
    )


def create_dust_cloud(
    particle_system: VoxelParticleSystem,
    position: LVector3f,
    color: LVector4f = LVector4f(0.7, 0.6, 0.5, 0.5)
):
    """Create dust cloud effect.
    
    Args:
        particle_system: Particle system to emit from
        position: Cloud position
        color: Dust color
    """
    particle_system.emit(
        position=position,
        velocity=LVector3f(0, 0, 0.5),
        color=color,
        size=0.15,
        lifetime=1.5,
        count=20,
        spread=0.8
    )
