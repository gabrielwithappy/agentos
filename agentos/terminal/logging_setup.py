from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from agentos.terminal.paths import agentos_home

LOG_FILENAME = "agentos.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 2

_configured = False


def logs_dir(home: str | Path | None = None) -> Path:
    return agentos_home(home) / "logs"


def log_file_path(home: str | Path | None = None) -> Path:
    return logs_dir(home) / LOG_FILENAME


def configure_logging(home: str | Path | None = None) -> Path:
    """Attaches a rotating file handler to the ``agentos`` logger tree.

    Idempotent: the TUI, hooks, and any subprocess entry points can all call
    this on startup without installing duplicate handlers. Errors that would
    otherwise only appear as a Textual worker traceback (with no way to
    inspect them after the terminal clears) land here instead.
    """
    global _configured
    path = log_file_path(home)
    if _configured:
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass

    handler = logging.handlers.RotatingFileHandler(
        path, maxBytes=MAX_LOG_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z")
    )

    logger = logging.getLogger("agentos")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

    _configured = True
    return path


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"agentos.{name}")


__all__ = ["configure_logging", "get_logger", "log_file_path", "logs_dir"]
