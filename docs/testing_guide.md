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

## Current Test Suite

### Phase 1 – Core Utilities and Physics

#### `tests/test_logger.py`

- **Purpose**: Verify that `util.logger.time_block` writes metrics to CSV even at DEBUG level.
- **Key fixtures**: `tmp_path`, `monkeypatch` to redirect the logs directory.
- **Assertions**:
  - `metrics.csv` is created.
  - Header row matches `["timestamp", "name", "value", "labels"]`.
  - The last row’s `name` column matches the block name.

#### `tests/test_physics.py`

- **Purpose**: Isolate and validate the kinematic physics logic without Ursina.
- **Fake entity**: `DummyEntity` with only a `.y` attribute.
- **Test cases**:
  1. `apply_gravity_respects_max_fall_speed`
  2. `integrate_vertical_snaps_to_ground`
  3. `jump_coyote_and_buffer_behavior`
- **What’s covered**:
  - Gravity clamping.
  - Ground snapping.
  - Jump buffering and coyote time.

### Phase 2 – Server Admin Commands

#### `tests/test_server_admin.py`

- **Purpose**: Test server-side admin command handling and host player state.
- **Fake writer**: `FakeWriter` mimics `asyncio.StreamWriter` for in-memory assertions.
- **Test cases**:
  1. `test_admin_list_includes_host_and_player`
  2. `test_admin_hostpos_and_hostrot_update_host_state`
  3. `test_admin_kick_removes_client_and_state`
- **What’s covered**:
  - `admin_command` → `admin_response` round trip.
  - Host player updates.
  - Client removal on `/kick`.

### Phase 3 – World and Chunk Loading

#### `tests/test_world_chunk_loading.py`

- **Purpose**: Test dynamic chunk loading, unloading, and world generation determinism.
- **No Ursina**: Tests use the World class but avoid rendering.
- **Test cases**:
  1. `test_get_player_chunk_coords` - Coordinate conversion
  2. `test_chunk_loading_on_update` - Chunks load on player movement
  3. `test_chunk_unloading_on_distance` - Distant chunks unload
  4. `test_chunk_generation_determinism` - Same coords = same terrain
  5. `test_chunk_loading_respects_max_per_frame` - Throttling works
  6. `test_chunk_load_radius` - Only loads within radius
  7. `test_height_function_consistency` - Terrain generation is stable
  8. `test_empty_world_after_init` - No premature generation
  9. `test_chunk_queues_clear_after_processing` - Queue management
- **What's covered**:
  - Dynamic chunk loading/unloading.
  - Deterministic terrain generation.
  - Performance throttling.
  - Memory management.

---

## How Tests Are Structured

- **No Ursina in unit tests**: All core logic tests avoid importing `ursina`.
- **Async tests**: Server admin tests use `asyncio.run` to call async methods.
- **Fixtures**: `tmp_path` and `monkeypatch` are used to avoid touching real files or global state.
- **Fake objects**: `FakeWriter` and `DummyEntity` provide the minimal interface needed.

---

## Extending the Test Suite

### Next Phase: Client Protocol (`tests/test_client_protocol.py`)

Add tests for `network/client.py`:

- `_handle_state_snapshot`:
  - Feed a mock snapshot with two players.
  - Assert `remote_players` dict is updated correctly.
  - Remove a player in a second snapshot; assert the entity is removed.
- `_handle_admin_response`:
  - Send an `admin_response` message.
  - Assert `client._admin_log` contains the lines in order.
- `send_admin_command`:
  - Verify the message placed on `send_queue` matches the expected JSON.

**Pattern**: Use the real `GameClient` class but avoid sockets by calling handlers directly.

### Next Phase: Headless Integration (`tests/test_integration_headless.py`)

Spin up a real server on a random port and connect a client:

```python
import asyncio
from engine.networking.server import GameServer
from engine.networking.client import GameClient

async def test_client_connects_and_receives_welcome():
    server = GameServer(host="127.0.0.1", port=0)  # port=0 picks a free port
    await server.start()
    addr = server.server.sockets[0].getsockname()
    client = GameClient(addr[0], addr[1])
    client.start()
    # Wait briefly, then assert client.player_id is set
    assert client.player_id is not None
    client.stop()
    server.running = False
    server.server.close()
```

- Use `pytest.mark.asyncio`.
- Keep the test short (connect, exchange one message, disconnect).

### Performance / Regression Tests

Add a `tests/test_performance.py`:

```python
def test_world_generate_baseline():
    from games.voxel_world.systems.world_gen import World
    world = World()
    with time_block("world_generate", logger, {"chunks": 9}):
        world.create_chunk(0, 0)
        # ... generate a few more chunks
    # Assert duration is below a soft threshold (e.g. 100 ms)
```

- Use `time_block` or `time.perf_counter` directly.
- Store thresholds in constants at the top of the file for easy tuning.

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

1. **Isolate the unit**: Avoid importing Ursina unless you’re testing an Ursina-specific feature.
2. **Use fakes**: Provide the smallest possible interface (e.g. `.y` for entities).
3. **Avoid real network I/O**: Call handlers directly or use `FakeWriter`.
4. **Prefer `tmp_path`**: Never write to the real `logs/` directory in tests.
5. **Keep async tests short**: Use `asyncio.run` for single calls; avoid long-running servers.
6. **Assert behavior, not implementation**: Test that the player ends up at the correct position, not that a specific internal variable was set.

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

2025-12-12
