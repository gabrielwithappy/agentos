import logging

import pytest

from agentos.terminal import logging_setup


@pytest.fixture(autouse=True)
def _reset_agentos_logger():
    logger = logging.getLogger("agentos")
    original_handlers = list(logger.handlers)
    original_propagate = logger.propagate
    yield
    for handler in logger.handlers:
        if handler not in original_handlers:
            handler.close()
    logger.handlers = original_handlers
    logger.propagate = original_propagate


def test_configure_logging_creates_log_file_and_writes_records(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "agentos-home"))
    monkeypatch.setattr(logging_setup, "_configured", False)

    path = logging_setup.configure_logging()
    assert path == tmp_path / "agentos-home" / "logs" / "agentos.log"
    assert path.parent.is_dir()

    logger = logging_setup.get_logger("test")
    logger.info("hello from test")
    for handler in logging.getLogger("agentos").handlers:
        handler.flush()

    assert "hello from test" in path.read_text(encoding="utf-8")


def test_configure_logging_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTOS_HOME", str(tmp_path / "agentos-home"))
    monkeypatch.setattr(logging_setup, "_configured", False)

    logging_setup.configure_logging()
    handler_count_after_first = len(logging.getLogger("agentos").handlers)
    logging_setup.configure_logging()
    handler_count_after_second = len(logging.getLogger("agentos").handlers)

    assert handler_count_after_first == handler_count_after_second
