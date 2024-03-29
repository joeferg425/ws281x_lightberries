"""Wraps rpi_ws281x module and provides a bunch of helpers.

See https://github.com/rpi-ws281x/rpi-ws281x-python for referenced module.
"""
from __future__ import annotations
import logging
from lightberries.array_controller import ArrayController as ArrayController  # noqa
from lightberries.matrix_controller import MatrixController as MatrixController  # noqa

# setup logging
LOGGER = logging.getLogger("lightBerries")
logging.addLevelName(5, "VERBOSE")
