# Shared physics constants for movement and water

# Acceleration (units per second^2) when on ground
ACCELERATION = 30.0

# Friction applied when no input (deceleration) (units per second^2)
FRICTION = 15.0

# Air control multiplier (0.0-1.0) – reduces acceleration when airborne
AIR_CONTROL = 0.5

# Base move speed (units per second) – max speed after acceleration
MOVE_SPEED = 6.0

# Water-specific multipliers
WATER_MULTIPLIER = 0.5  # Horizontal speed is halved in water
WATER_DRAG = 2.0        # Horizontal drag coefficient in water
