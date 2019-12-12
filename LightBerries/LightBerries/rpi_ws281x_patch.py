import logging

LOGGER = logging.getLogger(__name__)
logging.addLevelName(5, 'VERBOSE')
if not LOGGER.handlers:
	streamHandler = logging.StreamHandler()
	LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)

import sys
if sys.platform != 'linux':
	# this lets me debug in windows
	class rpi_ws281x:
		class PixelStrip:
			rpi_ws281x = None
			def __init__(self, *args, **kwargs):
				self.count = 0
				if 'num' in kwargs:
					self.count = kwargs['num']
			def begin(self):
				pass
			def setPixelColor(self, index, color):
				pass
			def show(self):
				pass
			def _cleanup(self):
				pass
			def numPixels(self):
				return self.count
	ws = rpi_ws281x

else:
	import rpi_ws281x
	import rpi_ws281x as ws

	def _monkeypatch__setitem__(self, pos, value):
		"""Set the 24-bit RGB color value at the provided position or slice of
		positions.

		joeferg425: MONKEY PATCH: calls to 'ws2811_led_set' needed to have the thrid argument forced to int type
		"""
		# Handle if a slice of positions are passed in by setting the appropriate
		# LED data values to the provided values.
		if isinstance(pos, slice):
			index = 0
			for n in xrange(*pos.indices(self.size)):
				ws.ws2811_led_set(self.channel, n, int(value[index]))
				index += 1
		# Else assume the passed in value is a number to the position.
		else:
			return ws.ws2811_led_set(self.channel, pos, int(value))


	try:
		rpi_ws281x.rpi_ws281x._LED_Data.__setitem__ = _monkeypatch__setitem__
	except Exception as ex:
		LOGGER.exception('Failed rpi_ws281x Monkey Patch: %s' % ex)
