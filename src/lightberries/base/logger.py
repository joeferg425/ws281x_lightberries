"""Logger setup."""

import logging
import sys

LOGGER = logging.getLogger("lightberries")
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(logging.CRITICAL)
