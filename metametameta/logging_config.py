"""
Logging configuration.
"""

import os
from typing import Any


def generate_config(level: str = "DEBUG") -> dict[str, Any]:
    """
    Generate a logging configuration.

    Returns:
        dict: The logging configuration.
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {"format": "[%(levelname)s] %(name)s: %(message)s"},
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(levelname)-8s%(reset)s %(green)s%(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": level,
                "formatter": "colored",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # Default is stderr
            },
        },
        "loggers": {
            "metametameta": {
                "handlers": ["default"],
                "level": level,
                "propagate": False,
            }
        },
    }
    if os.environ.get("NO_COLOR") or os.environ.get("CI"):
        config["handlers"]["default"]["formatter"] = "standard"
    return config
