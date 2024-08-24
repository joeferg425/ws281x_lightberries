"""Wraps rpi_ws281x module and provides a bunch of helpers.

See https://github.com/rpi-ws281x/rpi-ws281x-python for referenced module.
"""

from __future__ import annotations

import datetime
import logging
import random
from hashlib import sha256

from lightberries.array_controller import ArrayController as ArrayController

random.seed(
    int.from_bytes(sha256(str(datetime.datetime.now(tz=None)).encode(), usedforsecurity=False).digest(), "big")
)  # noqa: DTZ005
# from lightberries.matrix_controller import MatrixController as MatrixController

# setup logging
LOGGER = logging.getLogger("lightBerries")
logging.addLevelName(5, "VERBOSE")
if not LOGGER.handlers:
    stream_handler = logging.StreamHandler()
    LOGGER.addHandler(stream_handler)
LOGGER.setLevel(logging.INFO)
LOGGER.setLevel(logging.INFO)
