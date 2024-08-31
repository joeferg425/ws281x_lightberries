"""Defines callable behaviors for this module."""

# ruff: noqa: F401, PGH003, I001, F403
from __future__ import annotations

import logging

from lightberries.cli import CLI

LOGGER = logging.getLogger("lightBerries")

if __name__ == "__main__":  # pylint: disable=invalid-name
    CLI()
