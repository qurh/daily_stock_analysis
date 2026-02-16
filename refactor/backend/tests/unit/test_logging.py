import logging

from app.shared.logging_config import setup_logging


def test_setup_logging_sets_level() -> None:
    setup_logging(level="INFO")
    logger = logging.getLogger("m0-test")
    assert logger.getEffectiveLevel() <= logging.INFO
