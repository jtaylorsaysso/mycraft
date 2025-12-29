# Contributing to MyCraft

Thank you for your interest in contributing to MyCraft! Whether you're a playtester giving feedback, a developer fixing bugs, or a creator sharing ideas, we welcome your contributions.

---

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
- [Playtester Contributions](#playtester-contributions)
- [Developer Contributions](#developer-contributions)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

---

## Ways to Contribute

### 🎮 Playtesters

- Report bugs and issues
- Provide gameplay feedback
- Suggest features and improvements
- Test multiplayer and performance

### 💻 Developers

- Fix bugs and implement features
- Improve performance and optimization
- Write tests and documentation
- Review pull requests

### 📚 Documenters

- Improve guides and tutorials
- Write API documentation
- Create examples and demos
- Fix typos and clarify instructions

### 🎨 Creators

- Design new biomes and content
- Create custom textures and models
- Share gameplay ideas
- Build example games

---

## Playtester Contributions

### Reporting Bugs

Great bug reports include:

1. **Session Recording**: Check "Record" in the launcher before playing
2. **Steps to Reproduce**: What were you doing when it happened?
3. **Expected vs. Actual**: What should have happened? What actually happened?
4. **Environment**: Your OS, Python version, and preset used
5. **Logs and Screenshots**: Files from `logs/` and `recordings/` folders

**Example Bug Report**:

```
Title: Player falls through terrain in Canyon biome

Steps to Reproduce:
1. Launch with Creative preset
2. Fly to Canyon biome (around x=200, z=200)
3. Land on steep canyon wall
4. Player falls through the ground

Expected: Player should stand on the terrain
Actual: Player falls infinitely

Environment:
- OS: Windows 11
- Python: 3.12.3
- Preset: Creative
- Session: recordings/Player_1703123456.json

Logs attached: mycraft-20251221-093000.log
```

### Providing Feedback

We want to hear about:

- **First Impressions**: Was setup easy? What was confusing?
- **Gameplay Feel**: Is movement smooth? Are controls intuitive?
- **Performance**: Does it run well on your machine? Any lag or stuttering?
- **Multiplayer**: How was the connection? Any sync issues?
- **Fun Factor**: What's enjoyable? What's boring or frustrating?

**Where to Share**:

- GitHub Issues for bugs
- Discussions for feedback and ideas
- Direct message for quick notes

---

## Developer Contributions

### Setting Up Development Environment

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/mycraft.git
   cd mycraft
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests to verify setup**:

   ```bash
   pytest tests/ -v
   ```

   You should see 147 tests pass.

---

### Project Structure

```
mycraft/
├── engine/              # Core engine (ECS, physics, networking, rendering)
│   ├── ecs/            # Entity Component System
│   ├── physics/        # Physics and collision
│   ├── networking/     # Multiplayer and discovery
│   └── rendering/      # Panda3D rendering
├── games/              # Game implementations
│   └── voxel_world/   # Flagship voxel game
│       ├── systems/   # Game-specific systems
│       ├── biomes.py  # Terrain generation
│       └── blocks.py  # Block registry
├── tests/              # Test suite
├── docs/               # Documentation
└── config/             # Configuration files
```

**Key Principle**: The `engine/` is game-agnostic. Game-specific code goes in `games/voxel_world/`.

---

### Architecture Overview

MyCraft uses an **Entity Component System (ECS)** architecture:

- **Entities**: Unique IDs representing game objects (players, blocks, etc.)
- **Components**: Data containers (Position, Velocity, Health, etc.)
- **Systems**: Logic that operates on entities with specific components

**Example**:

```python
from engine.ecs.world import World
from engine.ecs.component import Component

# Define a component
class Position(Component):
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

# Create an entity
world = World()
player = world.create_entity()
world.add_component(player, Position(0, 10, 0))
```

See [docs/engine/ARCHITECTURE.md](docs/engine/ARCHITECTURE.md) for details.

---

## Code Style and Standards

### Python Style

- Follow **PEP 8** conventions
- Use **type hints** where practical
- Write **docstrings** for public functions and classes
- Keep functions focused and small (<50 lines when possible)

**Example**:

```python
def raycast_ground_height(
    world_pos: tuple[float, float, float],
    max_distance: float = 10.0
) -> tuple[float, tuple[float, float, float]] | None:
    """
    Raycast downward to find ground height and surface normal.
    
    Args:
        world_pos: (x, y, z) position to raycast from
        max_distance: Maximum raycast distance
        
    Returns:
        Tuple of (height, normal) if hit, None otherwise
    """
    # Implementation...
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `PlayerControlSystem`)
- **Functions/Variables**: `snake_case` (e.g., `raycast_ground_height`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_PLAYERS`)
- **Private**: Prefix with `_` (e.g., `_internal_helper`)

### File Organization

- One class per file when possible
- Group related functionality in modules
- Keep imports organized (stdlib, third-party, local)

---

## Testing

### Running Tests

Run the full test suite:

```bash
pytest tests/ -v
```

Run specific test file:

```bash
pytest tests/test_physics.py -v
```

Run with coverage:

```bash
pytest tests/ --cov=engine --cov=games/voxel_world --cov-report=term
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names that explain what's being tested

**Example**:

```python
def test_player_jumps_when_grounded():
    """Player should jump when grounded and jump input is pressed."""
    world = World()
    player = create_test_player(world, grounded=True)
    
    # Simulate jump input
    apply_jump_input(world, player)
    
    # Verify vertical velocity increased
    velocity = world.get_component(player, Velocity)
    assert velocity.y > 0, "Player should have upward velocity after jump"
```

### Test Categories

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test system interactions
- **Regression Tests**: Prevent previously fixed bugs from returning

---

## Submitting Changes

### Workflow

1. **Fork the repository** (if external contributor)

2. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation

4. **Run tests**:

   ```bash
   pytest tests/ -v
   ```

5. **Commit with clear messages**:

   ```bash
   git commit -m "Add slope sliding physics for steep terrain"
   ```

6. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** on GitHub

### Pull Request Guidelines

**Good PR Description**:

```
## Summary
Implements slope sliding physics when player is on terrain >45°

## Changes
- Modified `integrate_movement()` to apply sliding force
- Added `SLIDE_THRESHOLD` constant (45 degrees)
- Updated tests to verify sliding behavior

## Testing
- Added `test_player_slides_on_steep_slopes()`
- Verified existing physics tests still pass
- Manual testing in Canyon biome

## Related Issues
Fixes #42
```

**PR Checklist**:

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated if needed
- [ ] Code follows style guidelines
- [ ] Commit messages are clear

---

## Development Tips

### Hot-Reload Configuration

Edit `config/playtest.json` while the game is running to test parameter changes without restarting:

```json
{
  "movement_speed": 8.0,
  "jump_height": 4.0,
  "mouse_sensitivity": 50.0
}
```

Changes apply within 1 second.

### Debug Mode

Launch with debug flags for extra logging:

```bash
python run_client.py --preset testing --debug
```

Check `logs/` for detailed output.

### Performance Profiling

Use the built-in metrics system:

```python
from util.logger import time_block, log_metric

with time_block("chunk_generation", logger):
    generate_chunk(x, z)
```

Metrics are saved to `logs/metrics.csv`.

---

## Questions?

- **Technical Questions**: Open a GitHub Discussion
- **Bug Reports**: Create a GitHub Issue
- **Quick Questions**: Reach out directly

---

## Code of Conduct

Be respectful, constructive, and welcoming to all contributors. We're building this together!

---

**Thank you for contributing to MyCraft! 🎮**

*Last Updated: 2025-12-21*
