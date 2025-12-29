import logging
import csv
import time
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import glob
import os


_LOGGER_INITIALIZED = False
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_METRICS_FILE: Optional[Path] = None
_CSV_FIELDNAMES = ["timestamp", "name", "value", "labels"]


def _init_logging() -> None:
    """Initialize root logger and file handlers once."""
    global _LOGGER_INITIALIZED, _METRICS_FILE
    if _LOGGER_INITIALIZED:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = _LOG_DIR / f"mycraft-{time.strftime('%Y%m%d-%H%M%S')}.log"
    _METRICS_FILE = _LOG_DIR / "metrics.csv"

    logger = logging.getLogger("mycraft")
    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger.addHandler(ch)
    logger.addHandler(fh)

    # Prepare metrics CSV with header
    # Prepare metrics CSV with header
    if not _METRICS_FILE.exists():
        with _METRICS_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writeheader()

    # Log unhandled exceptions
    sys.excepthook = _handle_exception
    
    # Cleanup old logs
    _cleanup_old_logs()

    _LOGGER_INITIALIZED = True

def _handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception hook to log unhandled errors."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = logging.getLogger("mycraft")
    logger.critical("Uncaught Exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Print to stderr as well (default behavior)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def _cleanup_old_logs(keep: int = 10) -> None:
    """Keep only the N most recent log files."""
    try:
        log_files = sorted(
            glob.glob(str(_LOG_DIR / "mycraft-*.log")),
            key=os.path.getmtime
        )
        
        while len(log_files) > keep:
            oldest = log_files.pop(0)
            try:
                os.remove(oldest)
                print(f"Cleaned up old log: {oldest}")
            except OSError:
                pass
    except Exception as e:
        print(f"Failed to cleanup logs: {e}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a child logger under the 'mycraft' namespace."""
    _init_logging()
    base = logging.getLogger("mycraft")
    return base.getChild(name) if name else base


def log_metric(name: str, value: float, labels: Optional[Dict[str, Any]] = None) -> None:
    """Append a single metric sample to the CSV metrics file.

    Labels are stored as a simple key=value;... string for easy inspection.
    """
    _init_logging()
    if _METRICS_FILE is None:
        return

    label_str = ""
    if labels:
        # Flatten labels dict into key=value pairs
        parts = [f"{k}={v}" for k, v in labels.items()]
        label_str = ";".join(parts)

    row = {
        "timestamp": f"{time.time():.3f}",
        "name": name,
        "value": value,
        "labels": label_str,
    }

    try:
        with _METRICS_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writerow(row)
    except OSError:
        # Metrics should never crash the game
        pass


class time_block:
    """Context manager for timing small code sections and logging metric + message.

    Usage:
        logger = get_logger("world")
        with time_block("world_generate", logger, {"chunks": 9}):
            generate_chunks()
    """

    def __init__(
        self,
        name: str,
        logger: Optional[logging.Logger] = None,
        labels: Optional[Dict[str, Any]] = None,
        level: int = logging.INFO,
    ) -> None:
        self.name = name
        self.logger = logger or get_logger("telemetry")
        self.labels = labels or {}
        self.level = level
        self._start: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self._start) * 1000.0
        # Log human-readable message
        label_str = " ".join(f"{k}={v}" for k, v in self.labels.items())
        msg = f"{self.name} took {duration_ms:.2f} ms"
        if label_str:
            msg += f" ({label_str})"
        self.logger.log(self.level, msg)

        # Log to CSV metrics
        all_labels = dict(self.labels)
        all_labels.setdefault("event", self.name)
        log_metric(self.name, duration_ms, labels=all_labels)

