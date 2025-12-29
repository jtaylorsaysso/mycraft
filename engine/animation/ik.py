"""Inverse Kinematics system using FABRIK algorithm.

Provides IK solving for terrain-aware foot placement and hand reaching,
enabling natural character poses on uneven terrain.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from panda3d.core import LVector3f
import math

from engine.animation.core import Transform
from engine.animation.skeleton import Skeleton, Bone, BoneConstraints


@dataclass
class IKTarget:
    """Target position for IK solving.
    
    Represents a desired end-effector position (e.g., where a foot
    should touch the ground or where a hand should reach).
    """
    
    position: LVector3f
    bone_name: str  # End effector bone (e.g., "foot_left", "hand_right")
    weight: float = 1.0  # Blend weight (0-1)
    pole_target: Optional[LVector3f] = None  # Hint for joint orientation


class FABRIKSolver:
    """Forward And Backward Reaching Inverse Kinematics solver.
    
    FABRIK is an iterative IK algorithm that's faster and more stable
    than analytical methods. It works by:
    1. Forward pass: Move joints toward target from end to root
    2. Backward pass: Move joints back from root to maintain bone lengths
    3. Repeat until converged or max iterations reached
    """
    
    def __init__(self, tolerance: float = 0.01, max_iterations: int = 10):
        """Initialize FABRIK solver.
        
        Args:
            tolerance: Distance threshold for convergence (voxel units)
            max_iterations: Maximum solver iterations
        """
        self.tolerance = tolerance
        self.max_iterations = max_iterations
    
    def solve(
        self,
        chain: List[Bone],
        target_position: LVector3f,
        root_position: Optional[LVector3f] = None
    ) -> Dict[str, Transform]:
        """Solve IK for a bone chain.
        
        Args:
            chain: List of bones from root to end effector
            target_position: Desired end effector position
            root_position: Optional fixed root position
            
        Returns:
            Dictionary of bone transforms
        """
        if len(chain) < 2:
            return {}
        
        # Extract bone positions and lengths
        positions = []
        lengths = []
        
        for bone in chain:
            positions.append(LVector3f(
                bone.world_transform.position.x,
                bone.world_transform.position.y,
                bone.world_transform.position.z
            ))
            lengths.append(bone.length)
        
        # Store original root position
        if root_position is None:
            root_position = positions[0]
        
        # Check if target is reachable
        total_length = sum(lengths)
        distance_to_target = (target_position - root_position).length()
        
        if distance_to_target > total_length:
            # Target unreachable - stretch toward it
            direction = target_position - root_position
            dist = direction.length()
            if dist > 0:
                direction_normalized = LVector3f(
                    direction.x / dist,
                    direction.y / dist,
                    direction.z / dist
                )
            else:
                direction_normalized = LVector3f(0, 1, 0)
            
            positions[0] = root_position
            for i in range(len(chain) - 1):
                positions[i + 1] = positions[i] + direction_normalized * lengths[i]
        else:
            # Target reachable - run FABRIK iterations
            for iteration in range(self.max_iterations):
                # Forward pass: end to root
                positions[-1] = target_position
                for i in range(len(positions) - 2, -1, -1):
                    direction = positions[i] - positions[i + 1]
                    distance = direction.length()
                    if distance > 0:
                        direction_normalized = LVector3f(
                            direction.x / distance,
                            direction.y / distance,
                            direction.z / distance
                        )
                        positions[i] = positions[i + 1] + direction_normalized * lengths[i]
                
                # Backward pass: root to end
                positions[0] = root_position
                for i in range(len(positions) - 1):
                    direction = positions[i + 1] - positions[i]
                    distance = direction.length()
                    if distance > 0:
                        direction_normalized = LVector3f(
                            direction.x / distance,
                            direction.y / distance,
                            direction.z / distance
                        )
                        positions[i + 1] = positions[i] + direction_normalized * lengths[i]
                
                # Check convergence
                end_distance = (positions[-1] - target_position).length()
                if end_distance < self.tolerance:
                    break
        
        # Apply constraints
        positions = self._apply_constraints(chain, positions, root_position)
        
        # Convert positions to transforms
        return self._positions_to_transforms(chain, positions)
    
    def _apply_constraints(
        self,
        chain: List[Bone],
        positions: List[LVector3f],
        root_position: LVector3f
    ) -> List[LVector3f]:
        """Apply bone constraints to IK solution.
        
        Args:
            chain: Bone chain
            positions: Joint positions
            root_position: Fixed root position
            
        Returns:
            Constrained positions
        """
        # Re-run FABRIK with constraints
        for iteration in range(3):  # A few constraint passes
            # Forward pass with constraints
            positions[-1] = positions[-1]  # Keep end effector
            for i in range(len(positions) - 2, 0, -1):
                bone = chain[i]
                if bone.constraints:
                    # Calculate current rotation
                    direction = positions[i + 1] - positions[i - 1]
                    # Apply constraints (simplified - full implementation would use quaternions)
                    # For now, just preserve bone length
                    target_dir = positions[i + 1] - positions[i]
                    dist = target_dir.length()
                    if dist > 0:
                        target_dir_normalized = LVector3f(
                            target_dir.x / dist,
                            target_dir.y / dist,
                            target_dir.z / dist
                        )
                        positions[i] = positions[i + 1] - target_dir_normalized * chain[i - 1].length
            
            # Backward pass
            positions[0] = root_position
            for i in range(len(positions) - 1):
                direction = positions[i + 1] - positions[i]
                dist = direction.length()
                if dist > 0:
                    direction_normalized = LVector3f(
                        direction.x / dist,
                        direction.y / dist,
                        direction.z / dist
                    )
                    positions[i + 1] = positions[i] + direction_normalized * chain[i].length
        
        return positions
    
    def _positions_to_transforms(
        self,
        chain: List[Bone],
        positions: List[LVector3f]
    ) -> Dict[str, Transform]:
        """Convert joint positions to bone transforms.
        
        Args:
            chain: Bone chain
            positions: Joint positions
            
        Returns:
            Bone transforms
        """
        transforms = {}
        
        for i, bone in enumerate(chain):
            if i < len(positions):
                # Calculate rotation from bone direction
                if i < len(positions) - 1:
                    direction = positions[i + 1] - positions[i]
                    # Convert direction to rotation (simplified)
                    # Full implementation would use quaternions and proper rotation calculation
                    rotation = self._direction_to_rotation(direction)
                else:
                    rotation = LVector3f(0, 0, 0)
                
                transforms[bone.name] = Transform(
                    position=positions[i],
                    rotation=rotation,
                    scale=LVector3f(1, 1, 1)
                )
        
        return transforms
    
    def _direction_to_rotation(self, direction: LVector3f) -> LVector3f:
        """Convert direction vector to rotation angles.
        
        Args:
            direction: Direction vector
            
        Returns:
            Rotation as (heading, pitch, roll)
        """
        if direction.length() == 0:
            return LVector3f(0, 0, 0)
        
        # Calculate heading (Y-axis rotation in Panda3D)
        heading = math.degrees(math.atan2(direction.x, direction.y))
        
        # Calculate pitch (X-axis rotation)
        horizontal = math.sqrt(direction.x ** 2 + direction.y ** 2)
        pitch = math.degrees(math.atan2(-direction.z, horizontal))
        
        return LVector3f(heading, pitch, 0)


class IKLayer:
    """IK solving as an animation layer.
    
    Manages IK targets and solves for bone transforms, integrating
    with the LayeredAnimator system as the highest-priority layer.
    """
    
    def __init__(self, skeleton: Skeleton, solver: Optional[FABRIKSolver] = None):
        """Initialize IK layer.
        
        Args:
            skeleton: Skeleton to solve IK for
            solver: FABRIK solver (creates default if None)
        """
        self.skeleton = skeleton
        self.solver = solver or FABRIKSolver()
        self.targets: Dict[str, IKTarget] = {}
    
    def set_target(self, bone_name: str, position: LVector3f, weight: float = 1.0):
        """Set an IK target.
        
        Args:
            bone_name: End effector bone name
            position: Target position
            weight: Blend weight (0-1)
        """
        self.targets[bone_name] = IKTarget(
            position=position,
            bone_name=bone_name,
            weight=weight
        )
    
    def clear_target(self, bone_name: str):
        """Remove an IK target.
        
        Args:
            bone_name: End effector bone name
        """
        if bone_name in self.targets:
            del self.targets[bone_name]
    
    def clear_all_targets(self):
        """Remove all IK targets."""
        self.targets.clear()
    
    def update(self, dt: float, skeleton: Skeleton) -> Dict[str, Transform]:
        """Solve IK and return bone transforms.
        
        Args:
            dt: Delta time (unused for IK)
            skeleton: Skeleton to solve for
            
        Returns:
            Bone transforms from IK solving
        """
        transforms = {}
        
        for target in self.targets.values():
            if target.weight <= 0:
                continue
            
            # Get bone chain for this target
            try:
                chain = skeleton.get_chain(skeleton.root.name, target.bone_name)
                if len(chain) < 2:
                    continue
                
                # Solve IK for this chain
                ik_transforms = self.solver.solve(chain, target.position)
                
                # Blend transforms by weight
                for bone_name, transform in ik_transforms.items():
                    if target.weight < 1.0:
                        # Blend with existing transform (if any)
                        if bone_name in transforms:
                            # Simple lerp (full implementation would use slerp for rotations)
                            existing = transforms[bone_name]
                            transform = Transform(
                                position=existing.position + (transform.position - existing.position) * target.weight,
                                rotation=existing.rotation + (transform.rotation - existing.rotation) * target.weight,
                                scale=existing.scale
                            )
                    
                    transforms[bone_name] = transform
            
            except ValueError:
                # Chain not found - skip this target
                continue
        
        return transforms
