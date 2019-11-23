import os
import sys
import atexit
import inspect
import numpy as np
import enum
import time
import logging
from . import rpi_ws281x
from .Pixels import Pixel, PixelColors

LOGGER = logging.getLogger(__name__)
logging.addLevelName(5, 'VERBOSE')
if not LOGGER.handlers:
	streamHandler = logging.StreamHandler()
	LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)

class LightString:
	""" empty class prototype for typing """
	pass

class LightString(list):
	def __init__(self, ledCount:int=None, rpi_ws281x:rpi_ws281x=None, debug:bool=False):
		"""
		Creates a pixel array using the rpi_ws281x library and Pixels.

		ledCount: int
			the number of LEDs desired in the LightString

		rpi_ws281x: rpi_ws281x
			the ws281x object that actually controls the LED signaling

		debug: bool
			set true for debug messages
		"""
		if ledCount is None and rpi_ws281x is None:
			raise Exception('Cannot create LightString object without ledCount or rpi_ws281x object being specified')
		# self._gpioPin = gpioPin
		self._ledCount = ledCount
		# self._ledCount = ledCount
		# self._ledFrequency = ledFrequency
		# self._ledDMA = ledDMA
		# self._ledInvert = ledInvert
		# self._ledBrightness = int(255 * (ledPercentBrightness / 100))
		if True == debug:
			LOGGER.setLevel(logging.DEBUG)
			LOGGER.debug('%s.%s Debugging mode', self.__class__.__name__, inspect.stack()[0][3])
		self._ws281x = None
		if sys.platform == 'linux' and not os.getuid() == 0:
			raise Exception('GPIO functionality requires root privilege. Please run command again as root')
		try:
			if not rpi_ws281x is None:
				self._ws281x = rpi_ws281x# rpi_ws281x.Adafruit_NeoPixel(self._ledCount, self._gpioPin, self._ledFrequency, self._ledDMA, self._ledInvert, self._ledBrightness)
				self._ws281x.begin()
				self._ledCount = self._ws281x.numPixels()
			LOGGER.debug('%s.%s Created WS281X object', self.__class__.__name__, inspect.stack()[0][3])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise
		try:
			self._lights = np.array([Pixel() for i in range(self._ledCount)])
			LOGGER.debug('%s.%s Created Numpy Light array', self.__class__.__name__, inspect.stack()[0][3])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise
		# force cleanup of c objects
		atexit.register(self.__del__)
		# return self

	def __del__(self) -> None:
		"""
		Properly disposes of the rpi_ws281X object.
		Prevents (hopefully) memory leaks that were happening in the rpi_ws281x module.
		"""
		# super(LightString, self).__del__()
		if not self._ws281x is None:
			self.off()
			try:
				self._ws281x._cleanup()
			except SystemExit:
				raise
			except KeyboardInterrupt:
				raise
			except Exception as ex:
				LOGGER.error('Failed to clean up WS281X object: {}'.format(ex))
				raise
			self._ws281x = None

	def __len__(self) -> int:
		"""
		return length of the light string (the number of LEDs)
		"""
		return len(self._lights)

	def __getitem__(self, key) -> Pixel:
		"""
		return a LED(s) from array
		"""
		try:
			return self._lights[key].array
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Failed to get key "%s" from %s: %s', key, self._lights, ex)
			raise

	def __setitem__(self, key, value) -> None:
		"""
		set LED value(s) in array
		"""
		try:
			if isinstance(key, slice):
				self._lights.__setitem__(key, [Pixel(v) for v in value])
			else:
				self._lights.__setitem__(key, Pixel(value))
			# else:
				# super(LightString, self).__setitem__(key, value)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Failed to set light %s to value %s: %s', key, value, ex)
			raise

	def __enter__(self) -> LightString:
		"""
		"""
		return self

	def __exit__(self, *args) -> None:
		"""
		"""
		self.__del__()

	def setDebugLevel(self, level:int):
		"""
		set the logging level
		"""
		LOGGER.setLevel(level)

	def off(self):
		"""
		turn all of the LEDs in the LightString off
		"""
		for index in range(len(self._lights)):
			try:
				self[index] = 0#LightString(PixelColors.OFF)
			except SystemExit:
				raise
			except KeyboardInterrupt:
				raise
			except Exception as ex:
				LOGGER.error('Failed to set pixel %s in WS281X to value %s: %s', index, LightString(0), ex)
				raise
		self.refresh()

	def refresh(self):
		"""
		update ws281x signal using the numpy array
		"""
		for index, light in enumerate(self._lights):
			try:
				if index > 0:
					self._ws281x.setPixelColor(int(index), light._value)
				else:
					self._ws281x.setPixelColor(int(index), 0)
			except SystemExit:
				raise
			except KeyboardInterrupt:
				raise
			except Exception as ex:
				LOGGER.error('Failed to set pixel %s in WS281X to value %s: %s', index, light._value, ex)
				raise
		try:
			self._ws281x.show()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Function call "show" in WS281X object failed: {}'.format(ex))
			raise

if __name__ == '__main__':
	LOGGER.info('Running LightString')
	ledCount = 100
	ws281x = rpi_ws281x.Adafruit_NeoPixel(pin=18, dma=5, num=ledCount, freq_hz=800000)
	with LightString(rpi_ws281x=ws281x, debug=True) as l:
		l.refresh()
		p = LightString((255, 0, 0))
		l[4] = PixelColors.RED
		l.refresh()
		time.sleep(1)