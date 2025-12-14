# MyCraft Performance Baseline

This document describes how to capture baseline performance data using the built-in
logging and CSV metrics system.

## Outputs

- **Logs directory**: `logs/`
  - `mycraft-YYYYmmdd-HHMMSS.log` – human-readable logs
  - `metrics.csv` – machine-readable metrics (for spreadsheets/plots)

## Logging

The logging utilities live in `util/logger.py`.

- `get_logger(name: str | None)`
  - Returns a logger under the `mycraft` namespace (e.g. `mycraft.world`).
- `time_block(name, logger=None, labels=None)`
  - Context manager for timing code sections and emitting both log + CSV metric.
- `log_metric(name, value, labels=None)`
  - Append a single numeric metric sample to `metrics.csv`.

### Example Usage

```python
from util.logger import get_logger, time_block, log_metric

logger = get_logger("world")

# Timing a section (now per-chunk instead of all at once)
with time_block("chunk_create", logger, {"chunk_x": 0, "chunk_z": 0}):
    world.create_chunk(0, 0)

# Direct metric
log_metric("server_players", 4, {"source": "server_tick"})
```

## Interpreting Metrics

The `metrics.csv` file has four columns:

- `timestamp` – seconds since epoch (float)
- `name` – metric name (e.g. `world_generate`, `server_broadcast_ms`)
- `value` – numeric value (usually milliseconds or counts)
- `labels` – `key=value;...` labels string

You can load this file into:

- Excel / Google Sheets – for quick charts.
- Python / Pandas – for more advanced analysis.

## Suggested Baseline Scenarios

To establish a baseline, run these scenarios and save the resulting `logs/` folder:

1. **Single-player baseline**
   - Run `python run_client.py --host localhost --port 5420` with no server (or networking disabled).
   - Focus on world generation and rendering costs.

2. **Small LAN game (2–3 players)**
   - Start the server: `python run_server.py`.
   - Connect 2–3 clients from different machines.
   - Play for a few minutes and record metrics.

3. **Stress test (many clients)**
   - If possible, start multiple clients on the same LAN.
   - Focus on networking tick time and payload sizes.

## New Metrics (Chunk Loading System)

With dynamic chunk loading, the following metrics are now tracked:

- `chunk_create` - Time to generate a single chunk (ms)
- `chunks_loaded` - Counter for chunks loaded (with total_chunks label)
- `chunks_unloaded` - Counter for chunks unloaded (with total_chunks label)
- `chunk_mesh_triangles` - Triangle count per chunk

These metrics enable monitoring:
- Chunk generation performance over time
- Memory usage (via total_chunks)
- Mesh complexity trends

## Next Steps

- Monitor `chunk_create` timing to detect performance regressions
- Track `total_chunks` to understand memory scaling
- Use metrics to optimize chunk generation and meshing
- Compare performance before/after algorithm changes
