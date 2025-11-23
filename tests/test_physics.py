from engine.physics import (
    KinematicState,
    apply_gravity,
    integrate_vertical,
    simple_flat_ground_check,
    perform_jump,
    update_timers,
    register_jump_press,
    can_consume_jump,
)


class DummyEntity:
    def __init__(self, y: float = 0.0):
        self.y = y


def test_apply_gravity_respects_max_fall_speed():
    state = KinematicState(velocity_y=0.0)

    apply_gravity(state, dt=1.0, gravity=-10.0, max_fall_speed=-20.0)
    assert -20.0 < state.velocity_y <= -10.0

    # Apply again; velocity should clamp to max_fall_speed
    apply_gravity(state, dt=1.0, gravity=-10.0, max_fall_speed=-20.0)
    assert state.velocity_y == -20.0


def test_integrate_vertical_snaps_to_ground():
    entity = DummyEntity(y=5.0)
    state = KinematicState(velocity_y=-10.0, grounded=False)

    def ground_check(e):
        return simple_flat_ground_check(e, ground_height=2.0)

    integrate_vertical(entity, state, dt=1.0, ground_check=ground_check)

    assert entity.y == 2.0
    assert state.velocity_y == 0.0
    assert state.grounded is True


def test_jump_coyote_and_buffer_behavior():
    state = KinematicState(velocity_y=0.0, grounded=True)

    # Player presses jump while grounded
    register_jump_press(state)
    assert can_consume_jump(state, coyote_time=0.2, jump_buffer_time=0.2)

    # Move off ground and advance time beyond coyote/buffer windows
    state.grounded = False
    update_timers(state, dt=0.3)
    assert not can_consume_jump(state, coyote_time=0.2, jump_buffer_time=0.2)

    # Perform a jump and ensure state updates
    perform_jump(state, jump_height=5.0)
    assert state.velocity_y == 5.0
    assert state.grounded is False
