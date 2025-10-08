from __future__ import annotations

import logging
from logging.config import dictConfig


def setup_logging():
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": {"format": "%(levelname)s %(asctime)s %(name)s %(message)s"}},
            "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
            "root": {"level": "INFO", "handlers": ["console"]},
        }
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
