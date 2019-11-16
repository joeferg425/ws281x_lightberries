import sys
import atexit
if sys.platform != 'linux':
	# this lets me debug in windows
	class rpi_ws281x:
		class Adafruit_NeoPixel:
			def __init__(*args):
				pass
			def begin(self):
				pass
			def setPixelColor(self, index, color):
				pass
			def show(self):
				pass
			def _cleanup(self):
				pass
else:
	import rpi_ws281x
import numpy as np
import enum
import time
import logging
from Pixels import Pixel, PixelColors

LOGGER = logging.getLogger('Lights')
if not LOGGER.handlers:
	streamHandler = logging.StreamHandler()
	LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)

class LightString(dict):
	def __init__(self, gpioPin:int=18, ledCount:int=100, ledFrequency:int=800000, ledDMA:int=5, ledInvert:bool=False, ledPercentBrightness:int=80, verbose:bool=False):
		self._gpioPin = gpioPin
		self._ledCount = ledCount
		self._ledFrequency = ledFrequency
		self._ledDMA = ledDMA
		self._ledInvert = ledInvert
		self._ledBrightness = int(255 * (ledPercentBrightness / 100))
		if True == verbose:
			LOGGER.setLevel(logging.DEBUG)
			LOGGER.debug('Debugging mode')
		try:
			self._ws281x = rpi_ws281x.Adafruit_NeoPixel(self._ledCount, self._gpioPin, self._ledFrequency, self._ledDMA, self._ledInvert, self._ledBrightness)
			self._ws281x.begin()
			LOGGER.debug('Created WS281X object')
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Failed to create WS281X object: {}'.format(ex))
			raise
		try:
			self._lights = np.array([Pixel() for i in range(self._ledCount)])
			LOGGER.debug('Created Numpy Light array')
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Failed to create Numpy LED Array: {}'.format(ex))
			raise
		# force cleanup of c objects
		atexit.register(self.__del__)

	def __del__(self):
		if not self._ws281x is None:
			# self.SetLEDsOff()
			# self.RefreshLEDs()
			self.Off()
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

	def __len__(self):
		'''
		'''
		return self._ledCount

	def __getitem__(self, key):
		try:
			return self._lights[key]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Failed to get key "{}" from {}'.format(key, self._lights))
			raise

	def __setitem__(self, key, value):
		try:
			if isinstance(key, slice):
				self._lights.__setitem__(key, [Pixel(v) for v in value])
			else:
				self._lights.__setitem__(key, Pixel(value))
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Failed to set light {} to value {}: {}'.format(key, value, ex))
			raise

	def __enter__(self):
		'''
		'''
		return self

	def __exit__(self, *args):
		'''
		'''
		self.__del__()

	def Off(self):
		for index in range(len(self._lights)):
			try:
				self[index] = 0
			except SystemExit:
				raise
			except KeyboardInterrupt:
				raise
			except Exception as ex:
				LOGGER.error('Failed to set pixel {} in WS281X to value {}: {}'.format(index, Pixel(0), ex))
				raise
		self.Refresh()

	def Refresh(self):
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
				LOGGER.error('Failed to set pixel {} in WS281X to value {}: {}'.format(index, light._value, ex))
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
	with LightString(ledCount=5, verbose=True) as l:
	# l = LightString(ledCount=5, verbose=True)
		l.Refresh()
		p = Pixel((255, 0, 0))
		l[4] = PixelColors.RED
		l.Refresh()
		time.sleep(1)