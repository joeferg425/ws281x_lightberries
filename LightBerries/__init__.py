import sys
import logging
import LightBerries.LightControl
import LightBerries.LightFunctions
import LightBerries.LightPatterns
import LightBerries.LightStrings
import LightBerries.Pixels

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
