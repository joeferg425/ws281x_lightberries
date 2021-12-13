"""Wraps rpi_ws281x module and provides a bunch of helpers.

See https://github.com/rpi-ws281x/rpi-ws281x-python for referenced module.
"""
import sys
import logging
import LightBerries.LightPixels  # noqa F401
import LightBerries.LightPatterns  # noqa F401
import LightBerries.LightStrings  # noqa F401
import LightBerries.LightFunctions  # noqa F401
import LightBerries.LightControl  # noqa F401

# setup logging
LOGGER = logging.getLogger("LightBerries")
logging.addLevelName(5, "VERBOSE")
if not LOGGER.handlers:
    streamHandler = logging.StreamHandler()
    LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)
if sys.platform != "linux":
    fh = logging.FileHandler(__name__ + ".log")
else:
    fh = logging.FileHandler("/home/pi/" + __name__ + ".log")
fh.setLevel(logging.DEBUG)
LOGGER.addHandler(fh)
