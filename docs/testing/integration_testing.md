
# Integration Testing

Integration tests verify the interaction between the Client, Server, and Game World. These tests run in a headless environment using `pytest-asyncio`.

## Running Tests

To run the integration suite:

```bash
python3 -m pytest tests/test_integration_multiplayer.py tests/test_integration_world_sync.py -v
```

## Test Harness

The tests use a shared harness defined in `tests/test_utils/integration_harness.py`:

- **TestServerWrapper**: Wraps `GameServer`. Manages a background `asyncio` task for the server loop and monkey-patches `asyncio.start_server` to capture the ephemeral port.
- **TestClientWrapper**: Wraps `GameClient`. Connects to the server's ephemeral port and manages the client's receive loop.

## Test Coverage

### Multiplayer (`test_integration_multiplayer.py`)

- **Connection Flow**: Verifies client can connect and receive a welcome handshake.
- **Player Visibility**: Verifies that when a second player joins, the first player receives a `player_join` event.
- **Admin Commands**: Verifies that chat/admin commands effectively route from client to server and invoke callbacks.

### World Synchronization (`test_integration_world_sync.py`)

- **Block Updates**: Verifies that when the server broadcasts a block update, connected clients receive it and fire `on_block_update`.

## Known Limitations

- **Async Loop Conflicts**: The test harness relies on complex interaction between `unittest.IsolatedAsyncioTestCase` and the game's internal loops. In some environments, this can lead to hangs during teardown or connection attempts. If tests hang, try running them individually or restarting the environment.
- **Headless Limitations**: Visuals are not verified. We run in a headless environment without window creation.
