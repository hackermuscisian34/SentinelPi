import logging
from .config import config

def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler(config.LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )
