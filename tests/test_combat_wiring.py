"""Integration test for Combat Event Wiring."""
import sys
import unittest
from unittest.mock import MagicMock

# 1. Setup global mocks
class StubVec3:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = float(x), float(y), float(z)
    def __add__(self, other):
        return StubVec3(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other):
        return StubVec3(self.x - other.x, self.y - other.y, self.z - other.z)
    def lengthSquared(self):
        return self.x**2 + self.y**2 + self.z**2
    def normalize(self):
        l = (self.x**2 + self.y**2 + self.z**2)**0.5
        if l > 0:
            self.x /= l
            self.y /= l
            self.z /= l
    def dot(self, other):
        return self.x*other.x + self.y*other.y + self.z*other.z

mock_panda = MagicMock()
mock_panda.LVector3f = StubVec3
mock_panda.NodePath = MagicMock
mock_panda.CardMaker = MagicMock()
mock_panda.TransparencyAttrib = MagicMock()

sys.modules["panda3d"] = MagicMock()
sys.modules["panda3d.core"] = mock_panda
sys.modules["direct"] = MagicMock()
sys.modules["direct.showbase.ShowBase"] = MagicMock()

from engine.ecs.world import World
from engine.player_mechanics.context import PlayerContext
from engine.components.core import Transform, Health

class TestCombatWiring(unittest.TestCase):
    def test_damage_flow(self):
        """Test complete flow: Animation Event -> Attack Mechanic -> Damage."""
        from engine.player_mechanics.attack_mechanic import AttackMechanic
        
        # Setup World & Event Bus
        world = World()
        world.base = MagicMock() # Mock ShowBase
        
        # Create Player (Attacker)
        player_id = world.create_entity()
        transform = Transform(position=StubVec3(0, 0, 0))
        transform.node = MagicMock() # Mock the NodePath
        world.add_component(player_id, transform)
        
        # Create Enemy (Target)
        enemy_id = world.create_entity()
        # Enemy is 1 unit forward (within range and angle)
        world.add_component(enemy_id, Transform(position=StubVec3(0, 1, 0)))
        world.add_component(enemy_id, Health(current=100))
        
        # Setup AttackMechanic
        mechanic = AttackMechanic()
        mechanic.initialize(player_id, world)
        
        # Create PlayerContext for update
        ctx = PlayerContext(
            world=world,
            player_id=player_id,
            transform=world.get_component(player_id, Transform),
            state=MagicMock(),
            dt=0.016
        )
        # Mock input
        ctx.input = MagicMock()
        ctx.input.is_action_active.return_value = False
        
        # Mock relative vector for forward direction (0,1,0)
        world.base.render.getRelativeVector.return_value = StubVec3(0, 1, 0)
        
        # Track damage events
        damage_events = []
        def on_damage(event):
            damage_events.append(event)
        world.event_bus.subscribe("on_entity_damage", on_damage)
        
        # --- Step 1: Simulate "combat_hit_start" event from AnimationMechanic ---
        # (We skip AnimationMechanic here and just fire the global event it would fire)
        class HitStartEvent:
            entity_id = player_id
            damage_multiplier = 1.5
            
        world.event_bus.publish("combat_hit_start", 
            entity_id=player_id, 
            damage_multiplier=1.5
        )
        
        self.assertTrue(mechanic.hitbox_active)
        self.assertEqual(mechanic.current_multiplier, 1.5)
        
        # --- Step 2: Update Mechanic (Hit Detection) ---
        mechanic.update(ctx)
        
        # Should detect enemy and fire damage event
        self.assertEqual(len(damage_events), 1)
        self.assertEqual(damage_events[0].entity_id, enemy_id)
        self.assertEqual(damage_events[0].amount, 15.0) # 10 base * 1.5
        self.assertEqual(damage_events[0].source, player_id)
        self.assertIn(enemy_id, mechanic.hit_entities)
        
        # --- Step 3: Update again (Idempotency) ---
        mechanic.update(ctx)
        
        # Should NOT fire damage again for same entity
        self.assertEqual(len(damage_events), 1)
        
        # --- Step 4: End Hitbox ---
        world.event_bus.publish("combat_hit_end", entity_id=player_id)
        
        self.assertFalse(mechanic.hitbox_active)

if __name__ == '__main__':
    unittest.main()
