# Testing Guide

This guide explains how to run MyCraft’s test suite, what the current tests cover, and how to extend them as the project grows.

## Quick Start

### Prerequisites

- Python 3.12+
- Virtual environment activated (`source .venv/bin/activate`)
- `pytest` installed (it’s already in the venv)

### Running Tests

From the project root:

```bash
pytest
```

Run with verbose output:

```bash
pytest -vv
```

Run a specific test file:

```bash
pytest tests/test_physics.py
```

Run with coverage (if `pytest-cov` is installed):

```bash
pytest --cov=util --cov=engine --cov=network
```

---

## Current Test Suite Status

**Last Test Run:** 2025-12-28  
**Pass Rate:** 257/294 tests (87%)  
**Test Execution Time:** ~15 seconds

### Test Categories

#### ✅ Animation & Character (93 tests passing)

- `test_animation.py` - Animation state machine and transitions (20 tests)
- `test_animation_layers.py` - Layered animation system with bone masking (17 tests)
- `test_ik.py` - Inverse kinematics (14 tests)
- `test_skeleton.py` - Skeletal hierarchy and transforms (14 tests)
- `test_voxel_avatar.py` - Avatar creation and body parts (7 tests)
- `test_root_motion.py` - Root motion application (14 tests)
- `test_player_physics.py` - Player movement physics (9 tests)

#### ✅ Combat Systems (40+ tests passing)

- `game_tests/test_attack_system.py` - Attack mechanics and timing
- `game_tests/test_dodge_system.py` - Dodge mechanics and stamina
- `game_tests/test_parry_system.py` - Parry timing and windows
- `game_tests/test_stamina_system.py` - Stamina regeneration and costs

#### ✅ World & Terrain (30+ tests passing)

- `test_biomes.py` - Biome generation and height functions (14 tests)
- `test_blocks.py` - Block registry and properties (11 tests)

#### ✅ Physics & Collision (13 tests passing)

- `test_physics_raycast.py` - Raycast ground detection (4 tests)
- `test_camera.py` - Camera movement and updates (2 tests)
- `test_debug_movement.py` - Player control system integration (1 test)

#### ✅ Integration Tests (3 tests passing)

- `test_integration_multiplayer.py` - Client-server connection and player visibility (2 tests)
- `test_integration_world_sync.py` - Block update propagation (1 test)

#### ⏭️ Skipped Tests (12 tests)

- `test_world_chunk_loading.py` - Requires World API update for new chunk system

#### ❌ Remaining Failures (17 tests)

See [Tech Debt Register](tech_debt.md#test-suite-remaining-failures) for details.

### Mock Infrastructure

**Consolidated Mock Library:** `tests/test_utils/mock_panda.py`

Provides robust mocks for Panda3D types when testing without full Panda3D installation:

- `MockVector3` / `MockVector2` - Full vector arithmetic and operations
- `MockNodePath` - Scene graph hierarchy and transforms
- `MockCollisionHandlerQueue` / `MockCollisionTraverser` - Collision detection

**Benefits:**

- Tests run without Panda3D installation
- Consistent mock behavior across all test files
- Proper type handling prevents `TypeError` in arithmetic operations

---

## How Tests Are Structured

- **No Panda3D required for unit tests**: Core logic tests use mocks from `tests/test_utils/mock_panda.py`
- **Async integration tests**: Use `unittest.IsolatedAsyncioTestCase` for proper async/await support
- **Fixtures**: `tmp_path` and `monkeypatch` avoid touching real files or global state
- **Mock objects**: Provide minimal interface needed for testing

---

## Extending the Test Suite

### Adding New Tests

1. **Import shared mocks** from `tests/test_utils/mock_panda.py`:

   ```python
   from tests.test_utils.mock_panda import MockVector3, MockNodePath
   ```

2. **Use `unittest.TestCase`** for standard tests:

   ```python
   import unittest
   
   class TestMyFeature(unittest.TestCase):
       def test_something(self):
           self.assertEqual(expected, actual)
   ```

3. **Use `unittest.IsolatedAsyncioTestCase`** for async tests:

   ```python
   import unittest
   
   class TestAsyncFeature(unittest.IsolatedAsyncioTestCase):
       async def test_something(self):
           result = await async_function()
           self.assertEqual(expected, result)
   ```

### Performance / Regression Tests

Add benchmark tests in `tests/benchmarks/`:

- Requires `pytest-benchmark` package
- Use `@pytest.mark.benchmark` decorator
- Store baseline results for regression detection

---

## CI / Automation

### GitHub Actions (Optional)

If you want CI, add `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -e .
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=util --cov=engine --cov=network
```

### Pre-commit Hooks (Optional)

Add `pre-commit` to run tests locally before each push:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

---

## Tips for Writing New Tests

1. **Isolate the unit**: Use mocks from `tests/test_utils/mock_panda.py` instead of real Panda3D
2. **Use shared mocks**: Don't create local mock classes - extend the shared library
3. **Avoid real network I/O**: Call handlers directly or use test harnesses
4. **Prefer `tmp_path`**: Never write to real directories in tests
5. **Keep async tests short**: Use proper async/await patterns
6. **Assert behavior, not implementation**: Test outcomes, not internal state

---

## Future Test Extensions (Roadmap)

| Phase | Target | Example Tests |
|-------|--------|---------------|
| 3 | Client protocol | `test_state_snapshot_updates_remote_players`, `test_admin_response_log` |
| 3 | Headless integration | `test_server_client_handshake`, `test_admin_command_from_client` |
| 4 | Player/entity representation | `test_player_networking_rate_limit`, `test_remote_entity_lifecycle` |
| 5 | Performance regression | `test_server_tick_baseline`, `test_client_receive_rate` |

---

## Last Updated

2025-12-28
