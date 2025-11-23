import logging

from util import logger as logger_mod


def test_time_block_writes_metrics_csv(tmp_path, monkeypatch):
    """time_block should write a metrics row with the given name."""
    # Redirect logging output to a temporary log directory
    log_dir = tmp_path / "logs"

    monkeypatch.setattr(logger_mod, "_LOG_DIR", log_dir)
    monkeypatch.setattr(logger_mod, "_LOGGER_INITIALIZED", False)
    monkeypatch.setattr(logger_mod, "_METRICS_FILE", None)

    test_logger = logger_mod.get_logger("test")

    with logger_mod.time_block(
        "test_block",
        test_logger,
        {"foo": 1},
        level=logging.DEBUG,
    ):
        # No work needed; we only care that timing/metrics run
        pass

    metrics_file = log_dir / "metrics.csv"
    assert metrics_file.exists()

    rows = metrics_file.read_text(encoding="utf-8").strip().splitlines()
    # Header + at least one data row
    assert len(rows) >= 2

    header = rows[0].split(",")
    assert header == ["timestamp", "name", "value", "labels"]

    last = rows[-1].split(",")
    assert last[1] == "test_block"
