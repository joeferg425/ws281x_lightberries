import enum
import logging
import random
import inspect
from numpy import ndarray, array

LOGGER = logging.getLogger(__name__)
streamHandler = logging.StreamHandler()
LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)

class LED_ORDER(enum.Enum):
	RGB = [0,1,2]
	GRB = [1,0,2]

class Pixel:
	'''
	empty class prototype for typing
	'''
	pass

class Pixel():
	def __init__(self, rgb:any=None, order:LED_ORDER=LED_ORDER.GRB):
		try:
			self._value = 0
			self._order = order
			if rgb is None:
				self._value = 0
			elif isinstance(rgb, int) and rgb >= 0 and rgb <= 0xFFFFFF:
				self._value = rgb
			elif (isinstance(rgb, tuple) or isinstance(rgb, list) or isinstance(rgb, ndarray)) and len(rgb) == 3:
				x0 = (rgb[self._order.value[0]] << 16)
				x1 = (rgb[self._order.value[1]] << 8)
				x2 = (rgb[self._order.value[2]])
				self._value = (rgb[self._order.value[0]] << 16) + (rgb[self._order.value[1]] << 8) + (rgb[self._order.value[2]])
			elif isinstance(rgb, PixelColors):
				self._value = rgb.value._value
			elif isinstance(rgb, Pixel):
				self._value = rgb._value
			else:
				raise Exception('%s.%s Exception: Cannot assign pixel value using value: %s' % (self.__class__.__name__, inspect.stack()[0][3], rgb))
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def __len__(self) -> int:
		'''
		return the length of the pixel color array
		'''
		return 3

	def __int__(self) -> int:
		'''
		return the pixel as an RGB value
		'''
		return self._value

	def __str__(self) -> str:
		x=(self._value & 0xFF0000) >> 16, (self._value & 0xFF00) >> 8, self._value & 0xFF
		return '#{:02X}{:02X}{:02X}'.format(x[self._order.value[0]], x[self._order.value[1]], x[self._order.value[2]])

	def __repr__(self) -> str:
		return '<{}> {}'.format(self.__class__.__name__, str(self))

	@property
	def Tuple(self) -> tuple:
		x = ((self._value & 0xFF0000) >> 16, (self._value & 0xFF00) >> 8, self._value & 0xFF)
		return (x[self._order.value[0]], x[self._order.value[1]], x[self._order.value[2]])

	def FadeToColor(self, fadeToColor:Pixel, fadeStep:int):
		fadeToColor=Pixel(fadeToColor)
		for rgbIndex in self.Tuple:
			if self.Tuple[rgbIndex] != fadeToColor.Tuple[rgbIndex]:
				if self.Array[rgbIndex] - fadeStep > fadeToColor[rgbIndex]:
					self.Array[rgbIndex] -= fadeStep
				elif self.Array[rgbIndex] + fadeStep < fadeToColor[rgbIndex]:
					self.Array[rgbIndex] += fadeStep
				else:
					self.Array[rgbIndex] = fadeToColor[rgbIndex]

	@property
	def Array(self) -> array:
		return array(self.Tuple)

class PixelColors(enum.Enum):
	OFF     = Pixel((0,   0,   0  ))
	RED2    = Pixel((128, 0,   0  ))
	RED     = Pixel((255, 0,   0  ))
	ORANGE2 = Pixel((128, 128, 0  ))
	ORANGE  = Pixel((255, 128, 0  ))
	YELLOW  = Pixel((255, 210, 80 ))
	LIME    = Pixel((128, 255, 0  ))
	GREEN2  = Pixel((0,   128, 0  ))
	GREEN   = Pixel((0,   255, 0  ))
	TEAL    = Pixel((0,   255, 128))
	CYAN2   = Pixel((0,   128, 128))
	CYAN    = Pixel((0,   255, 255))
	SKY     = Pixel((0,   128, 255))
	BLUE    = Pixel((0,   0,   255))
	BLUE2   = Pixel((0,   0,   128))
	VIOLET  = Pixel((128, 0,   255))
	PURPLE  = Pixel((128, 0,   128))
	MIDNIGHT= Pixel((70,  0,   128))
	MAGENTA = Pixel((255, 0,   255))
	PINK    = Pixel((255, 0,   128))
	WHITE   = Pixel((255, 255, 255))
	GRAY    = Pixel((128, 118, 108))

	@ classmethod
	def RANDOM(self):
		randomColor = list(PixelColors)[random.randint(0,len(PixelColors)-1)]
		while randomColor == PixelColors.OFF:
			 randomColor = list(PixelColors)[random.randint(0,len(PixelColors)-1)]
		return randomColor
