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

# Slope physics
MAX_WALKABLE_SLOPE = 45.0   # degrees - slopes steeper than this cause sliding
SLIDE_FRICTION = 5.0        # friction coefficient when sliding down slopes
SLIDE_ACCELERATION = 15.0   # units/s² - downslope acceleration when sliding
SLIDE_CONTROL = 0.3         # 0.0-1.0 - player control multiplier while sliding
