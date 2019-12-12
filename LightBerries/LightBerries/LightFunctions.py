import sys
import numpy as np
import time
import random
import logging
import inspect
from typing import List, Tuple, Optional
from .rpi_ws281x_patch import rpi_ws281x
from .Pixels import Pixel, PixelColors
from .LightStrings import LightString
from .LightPatterns import LightPattern
from .LightDatas import LightData

LOGGER = logging.getLogger()
logging.addLevelName(5, 'VERBOSE')
if not LOGGER.handlers:
	streamHandler = logging.StreamHandler()
	LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)
import sys
if sys.platform != 'linux':
	fh = logging.FileHandler(__name__+'.log')
else:
	fh = logging.FileHandler('/home/pi/' + __name__+'.log')
fh.setLevel(logging.DEBUG)
LOGGER.addHandler(fh)

DEFAULT_TWINKLE_CHANCE = 0.0
DEFAULT_TWINKLE_COLOR = PixelColors.GRAY
DEFAULT_BACKGROUND_COLOR = PixelColors.OFF
DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.RED, PixelColors.WHITE, PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN]
DEFAULT_REFRESH_DELAY = 50

class LightFunction:
	"""
	"""
	def __init__(self, ledCount:int, pwmGPIOpin:int, channelDMA:int, frequencyPWM:int, invertSignalPWM:bool=False, ledBrightnessFloat:float=1, channelPWM:int=0, stripTypeLED=None, gamma=None, debug:bool=False, verbose:bool=False):
		"""
		Create a LightFunction object for running patterns across a rpi_ws281x LED string

		ledCount: int
			the number of Pixels in your string of LEDs
		pwmGPIOpin: int
			the GPIO pin number your lights are hooked up to (18 is a good choice since it does PWM)
		channelDMA: int
			the DMA channel to use (5 is a good option)
		frequencyPWM: int
			try 800,000
		invertSignalPWM: bool
			set true to invert the PWM signal
		ledBrightnessFloat: float
			set to a value between 0.0 (OFF), and 1.0 (ON)
			This setting tends to introduce flicker the lower it is
		channelPWM: int
			defaults to 0, see https://github.com/rpi-ws281x/rpi-ws281x-python
		stripTypeLED:
			see https://github.com/rpi-ws281x/rpi-ws281x-python
		gamma:
			see https://github.com/rpi-ws281x/rpi-ws281x-python
		debug: bool
			set true for some debugging messages
		verbose: bool
			set true for even more information
		"""
		try:
			if True == debug or True == verbose:
				LOGGER.setLevel(logging.DEBUG)
			if True == verbose:
				LOGGER.setLevel(5)
			self._LEDArray = LightString(pixelStrip=rpi_ws281x.PixelStrip(pin=pwmGPIOpin, dma=channelDMA, num=ledCount, freq_hz=frequencyPWM, channel=channelPWM, invert=invertSignalPWM, gamma=gamma, strip_type=stripTypeLED, brightness=int(255*ledBrightnessFloat)), debug=verbose)

			if True == verbose:
				self._LEDArray.setDebugLevel(5)
			self._LEDCount = len(self._LEDArray)
			self._VirtualLEDArray = LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=PixelColors.OFF)
			self._VirtualLEDBuffer = np.copy(self._VirtualLEDArray)
			self._VirtualLEDCount = len(self._VirtualLEDArray)
			self._VirtualLEDIndexArray = np.array(range(len(self._LEDArray)))
			self._VirtualLEDIndexCount = len(self._VirtualLEDIndexArray)
			self._LastModeChange = None
			self._NextModeChange = None
			self._FunctionList = []
			self._colorFunction = None
			self._overlayColorFunction = None

			self.__refreshDelay = 0.001
			self.__secondsPerMode = 120
			self.__backgroundColor = PixelColors.OFF
			self.__colorSequence = LightPattern.ConvertPixelArrayToNumpyArray([])
			self.__colorSequenceCount = 0
			self.__colorSequenceIndex = 0
			self.__overlayColorSequence = LightPattern.ConvertPixelArrayToNumpyArray([])
			self.__overlayColorSequenceCount = 0
			self.__overlayColorSequenceIndex = 0

			self._LoopForever = False
			self._OverlayList = []
			self._TwinkleChance = 0.0
			# self._TwinkleColorList = [PixelColors.WHITE]
			self._BlinkChance = 0.0
			self._BlinkColorList = [PixelColors.OFF]
			self._Blink = False
			self._RandomColors = False
			self._ShiftAmount = 0
			self._ShiftCount = 0
			self._ShiftCounter = 0
			self._flipLength = 0
			self._RandomChangeChance = 0.0
			self._AccelerateIndex = 0
			self._AccelerateDirection = 0
			self._MeteorCount = 0
			self._LightDataObjects = []
			self._MaxSpeed = 0
			self._CycleColors = False
			self._FadeAmount = 0

			self.reset()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def __del__(self):
		"""
		disposes of the rpi_ws281x object (if it exists) to prevent memory leaks
		"""
		try:
			if hasattr(self, '_LEDArray') and not self._LEDArray is None:
				del(self._LEDArray)
				self._LEDArray = None
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	@property
	def refreshDelay(self)->float:
		return self.__refreshDelay
	@refreshDelay.setter
	def refreshDelay(self, delay):
		self.__refreshDelay = float(delay)

	@property
	def backgroundColor(self)->Pixel:
		return self.__backgroundColor
	@backgroundColor.setter
	def backgroundColor(self, color:Pixel):
		self.__backgroundColor = Pixel(color).array

	@property
	def secondsPerMode(self)->float:
		return self.__secondsPerMode
	@secondsPerMode.setter
	def secondsPerMode(self, seconds:float):
		self.__secondsPerMode = float(seconds)

	@property
	def colorSequence(self)->np.ndarray:
		return self.__colorSequence
	@colorSequence.setter
	def colorSequence(self, colorSequence:List[Pixel]):
		if not callable(colorSequence):
			self.__colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			self.colorSequenceCount = len(self.__colorSequence)
			self.colorSequenceIndex = 0
		else:
			self.__colorSequence = colorSequence
			self.colorSequenceCount = None
			self.colorSequenceIndex = None

	@property
	def colorSequenceCount(self)->int:
		return self.__colorSequenceCount
	@colorSequenceCount.setter
	def colorSequenceCount(self, colorSequenceCount:int):
		self.__colorSequenceCount = colorSequenceCount

	@property
	def colorSequenceIndex(self)->int:
		return self.__colorSequenceIndex
	@colorSequenceIndex.setter
	def colorSequenceIndex(self, colorSequenceIndex:int):
		self.__colorSequenceIndex = colorSequenceIndex

	@property
	def colorSequenceNext(self):
		if not callable(self.colorSequence):
			temp = self.colorSequence[self.colorSequenceIndex]
			self.colorSequenceIndex += 1
			if self.colorSequenceIndex >= self.colorSequenceCount:
				self.colorSequenceIndex = 0
		else:
			temp = self.colorSequence().array
		return temp


	@property
	def overlayColorSequence(self)->np.ndarray:
		return self.__overlayColorSequence
	@overlayColorSequence.setter
	def overlayColorSequence(self, overlayColorSequence:List[Pixel]):
		if not callable(overlayColorSequence):
			self.__overlayColorSequence = LightPattern.ConvertPixelArrayToNumpyArray(overlayColorSequence)
			self.overlayColorSequenceCount = len(self.__overlayColorSequence)
			self.overlayColorSequenceIndex = 0
		else:
			self.__overlayColorSequence = overlayColorSequence
			self.overlayColorSequenceCount = None
			self.overlayColorSequenceIndex = None

	@property
	def overlayColorSequenceCount(self)->int:
		return self.__overlayColorSequenceCount
	@overlayColorSequenceCount.setter
	def overlayColorSequenceCount(self, overlayColorSequenceCount:int):
		self.__overlayColorSequenceCount = overlayColorSequenceCount

	@property
	def overlayColorSequenceIndex(self)->int:
		return self.__overlayColorSequenceIndex
	@overlayColorSequenceIndex.setter
	def overlayColorSequenceIndex(self, overlayColorSequenceIndex:int):
		self.__overlayColorSequenceIndex = overlayColorSequenceIndex

	@property
	def overlayColorSequenceNext(self):
		if not callable(self.overlayColorSequence):
			temp = self.overlayColorSequence[self.overlayColorSequenceIndex]
			self.overlayColorSequenceIndex += 1
			if self.overlayColorSequenceIndex >= self.overlayColorSequenceCount:
				self.overlayColorSequenceIndex = 0
		else:
			temp = self.overlayColorSequence().array
		return temp



	def reset(self):
		try:
			self._FunctionList = []
			self._OverlayList = []
			self._TwinkleColorList = []
			self._BlinkColorList = []
			self._LightDataObjects = []
			self._TwinkleChance = 0
			self._BlinkChance = 0
			self._colorFunction = None
			self._overlayColorFunction = None
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _initializeFunction(self, refreshDelay, functionPointer, configurationPointer, *args, **kwargs):
		try:
			self.refreshDelay = refreshDelay
			self._FunctionList = [(functionPointer, configurationPointer, args, kwargs)]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _initializeOverlay(self, functionPointer, configurationPointer, *args, **kwargs):
		try:
			self._OverlayList = [(functionPointer, configurationPointer, args, kwargs)]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _initializePattern(self, backgroundColor, ledArray):
		try:
			self.backgroundColor = backgroundColor
			self._SetVirtualLEDArray(ledArray)
			self._ShiftCount = 0
			self._FunctionList = []
			self._OverlayList = []
			self._TwinkleChance = 0
			self._TwinkleColorList = []
			self._LightDataObjects = []
			self._AccelerateIndex = 0
			self._colorSequenceIndex = 0
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _SetVirtualLEDArray(self, ledArray:List[List[int]]) -> None:
		"""
		"""
		try:
			if ledArray is None:
				self._VirtualLEDArray = LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor)
			elif len(ledArray) < self._LEDCount:
				self._VirtualLEDArray = LightPattern.PixelArray(arrayLength=self._LEDCount)
				x = LightPattern.ConvertPixelArrayToNumpyArray(ledArray)
				self._VirtualLEDArray[:len(ledArray)] = LightPattern.ConvertPixelArrayToNumpyArray(ledArray)
			else:
				self._VirtualLEDArray = LightPattern.ConvertPixelArrayToNumpyArray(ledArray)
			# assign new LED array to virtual LEDs
			self._VirtualLEDBuffer = np.copy(self._VirtualLEDArray)
			self._VirtualLEDCount = len(self._VirtualLEDArray)
			# set our indices for virtual LEDs
			self._VirtualLEDIndexCount = self._VirtualLEDCount
			self._VirtualLEDIndexArray = np.array(range(self._VirtualLEDIndexCount))
			# if the array is smaller than the actual light strand, make our entire strand addressable
			if self._VirtualLEDIndexCount < self._LEDCount:
				self._VirtualLEDIndexCount = self._LEDCount
				self._VirtualLEDIndexArray = np.array(range(self._VirtualLEDIndexCount))
				self._VirtualLEDArray = np.concatenate((self._VirtualLEDArray, np.array([PixelColors.OFF.tuple for i in range(self._LEDCount - len(self._VirtualLEDArray))])))
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _CopyVirtualLedsToWS281X(self, led_array=None):
		"""
		Sets each LED on the LED string to an array value

		Parameters:
			led_array list(tuple(int,int,int))
				array of LED color tuples
		"""
		try:
			if led_array is None:
				led_array = self._VirtualLEDArray
			# update the WS281X strand using the RGB array and the virtual LED indices
			self._LEDArray[:] = [led_array[self._VirtualLEDIndexArray[i]] for i in range(self._LEDCount)]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RefreshLEDs(self):
		"""
		Display current LED NeoPixel buffer
		"""
		try:
			self._LEDArray.refresh()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _off(self):
		"""
		"""
		try:
			self._VirtualLEDArray *= 0
			self._VirtualLEDArray[:] += self.backgroundColor
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RunConfigurations(self):
		try:
			for function in self._FunctionList:
				function[1](*function[2], **function[3])
			for function in self._OverlayList:
				function[1](*function[2], **function[3])
			self._colorFunction['function'](**{k:v for k,v in self._colorFunction.items() if k !='function'})
			if not self._overlayColorFunction is None:
				self._overlayColorFunction['function'](**{k:v for k,v in self._overlayColorFunction.items() if k !='function'})
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RunFunctions(self):
		try:
			for function in self._FunctionList:
				function[0]()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RunOverlays(self):
		try:
			for overlay in self._OverlayList:
				overlay[0]()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _GetRandomIndices(self, getChance:float=0.1):
		try:
			maxVal = 1000
			temp = []
			for LEDIndex in range(self._VirtualLEDCount):
				doLight = random.randint(0, maxVal)
				if doLight > maxVal * (1.0 - getChance):
					temp.append(LEDIndex)
			return temp
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Fade(self, fadeIndices:List[int]=None, fadeAmount:int=None, fadeColor:Pixel=None):
		"""
		"""
		if fadeIndices is None:
			fadeIndices = [i for i in range(self._VirtualLEDCount)]
		if fadeAmount is None:
			fadeAmount = self._FadeAmount
		if fadeColor is None:
			fadeColor = self.backgroundColor
		try:
			[self._FadeLED(i, fadeColor, fadeAmount) for i in fadeIndices]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _FadeOff(self, fadeAmount=None):
		if fadeAmount is None:
			fadeAmount = self._FadeAmount
		self._VirtualLEDArray[:] = self._VirtualLEDArray * ((255 - fadeAmount) / 255)

	def _FadeLED(self, led_index:int, offColor:Pixel=None, fadeAmount:int=None):
		try:
			if offColor is None:
				offColor = self.backgroundColor
			if fadeAmount is None:
				fadeAmount = self._FadeAmount
			offColor = Pixel(offColor).array
			self._VirtualLEDArray[led_index] = self._FadeColor(self._VirtualLEDArray[led_index], offColor, fadeAmount)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _FadeColor(self, color:Pixel, offColor:Pixel=None, fadeAmount:int=None):
		try:
			if offColor is None:
				offColor = self.backgroundColor
			if fadeAmount is None:
				fadeAmount = self._FadeAmount
			color = Pixel(color).array
			offColor = Pixel(offColor).array
			for rgbIndex in range(len(color)):
				if color[rgbIndex] != offColor[rgbIndex]:
					if color[rgbIndex] - fadeAmount > offColor[rgbIndex]:
						color[rgbIndex] -= fadeAmount
					elif color[rgbIndex] + fadeAmount < offColor[rgbIndex]:
						color[rgbIndex] += fadeAmount
					else:
						color[rgbIndex] = offColor[rgbIndex]
			return color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise




	def run(self):
		try:
			if self._NextModeChange is None:
				self._LastModeChange = time.time()
				if self.secondsPerMode is None:
					self._NextModeChange = self._LastModeChange + (random.uniform(30,120) )
				else:
					self._NextModeChange = self._LastModeChange + (self.secondsPerMode )
			self._RunConfigurations()
			while time.time() < self._NextModeChange or self._LoopForever:
				try:
					self._RunFunctions()
					self._CopyVirtualLedsToWS281X()
					self._RunOverlays()
					self._RefreshLEDs()
					time.sleep(self.refreshDelay)
				except KeyboardInterrupt:
					raise
				except SystemExit:
					raise
				except Exception as ex:
					LOGGER.exception('_Run Loop Error: {}'.format(ex))
					raise
			self._LastModeChange = time.time()
			if self.secondsPerMode is None:
				self._NextModeChange = self._LastModeChange + (random.random(30,120) )
			else:
				self._NextModeChange = self._LastModeChange + (self.secondsPerMode )
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise



	def useColorSingle(self, foregroundColor:Pixel=DEFAULT_COLOR_SEQUENCE[0], twinkleColors:bool=False)->None:
		"""
		Sets the the color sequence used by light functions to a single color of your choice

		foregroundColor:Pixel
			the color that each pixel will be set to

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				self.colorSequence = LightPattern.ConvertPixelArrayToNumpyArray([foregroundColor])
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				self._colorFunction = {'function':self.useColorSingle, 'foregroundColor':self.colorSequence[0]}
			elif twinkleColors == True:
				self.overlayColorSequence = LightPattern.ConvertPixelArrayToNumpyArray([foregroundColor])
				self._overlayColorFunction = {'function':self.useColorSingle, 'foregroundColor':self.colorSequence[0], 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSinglePseudoRandom(self, twinkleColors:bool=False)->None:
		"""
		Sets the the color sequence used by light functions to a single random named color

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				self.colorSequence = [PixelColors.pseudoRandom()]
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				self._colorFunction = {'function':self.useColorSinglePseudoRandom}
			elif twinkleColors == True:
				self.overlayColorSequence = [PixelColors.pseudoRandom()]
				self._overlayColorFunction = {'function':self.useColorSinglePseudoRandom, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSingleRandom(self, twinkleColors:bool=False)->None:
		"""
		Sets the the color sequence used by light functions to a single random RGB value

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				self.colorSequence = [PixelColors.random()]
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				self._colorFunction = {'function':self.useColorSingleRandom}
			elif twinkleColors == True:
				self.overlayColorSequence = [PixelColors.random()]
				self._overlayColorFunction = {'function':self.useColorSingleRandom, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSequence(self, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE, twinkleColors:bool=False)->None:
		"""
		Sets the the color sequence used by light functions to one of your choice

		colorSequence:List[Pixel]
			list of colors in the pattern

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				self.colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorSequence, 'colorSequence':self.colorSequence}
			elif twinkleColors == True:
				self.overlayColorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
				self._overlayColorFunction = {'function':self.useColorSequence, 'colorSequence':self.colorSequence, 'twinkleColors':True}
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorPseudoRandomSequence(self, sequenceLength:int=None, twinkleColors:bool=False)->None:
		"""
		Sets the color sequence used in light functions to a random list of named colors

		sequenceLength:int
			the number of random colors to use in the generated sequence

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if sequenceLength is None:
				sequenceLength = random.randint(self._LEDCount//20, self._LEDCount //10)
			self.backgroundColor = backgroundColor=PixelColors.OFF
			if twinkleColors == False:
				self.colorSequence = [PixelColors.pseudoRandom() for i in range(sequenceLength)]
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorPseudoRandomSequence, 'sequenceLength':sequenceLength}
			elif twinkleColors == True:
				self.overlayColorSequence = [PixelColors.pseudoRandom() for i in range(sequenceLength)]
				self._overlayColorFunction = {'function':self.useColorPseudoRandomSequence, 'sequenceLength':sequenceLength, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorPseudoRandom(self, twinkleColors:bool=False)->None:
		"""
		Sets the color sequence to generate a random named color every time one is needed in a function

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor=PixelColors.OFF
			if twinkleColors == False:
				self.colorSequence = PixelColors.pseudoRandom
				self.colorSequenceCount = random.randint(2,7)
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				self._colorFunction = {'function':self.useColorPseudoRandom}
			elif twinkleColors == True:
				self.overlayColorSequence = PixelColors.pseudoRandom
				self.overlayColorSequenceCount = random.randint(2,7)
				self._overlayColorFunction = {'function':self.useColorPseudoRandom, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorRandomSequence(self, sequenceLength:int=None, twinkleColors:bool=False)->None:
		"""
		Sets the color sequence used in light functions to a random list of RGB values

		sequenceLength:int
			the number of random colors to use in the generated sequence

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor=PixelColors.OFF
			if twinkleColors == False:
				if sequenceLength is None:
					sequenceLength = random.randint(self._LEDCount//20, self._LEDCount //10)
				self.colorSequence = [PixelColors.random() for i in range(sequenceLength)]
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorRandomSequence, 'sequenceLength':sequenceLength}
			elif twinkleColors == True:
				if sequenceLength is None:
					sequenceLength = random.randint(self._LEDCount//20, self._LEDCount //10)
				self.overlayColorSequence = [PixelColors.random() for i in range(sequenceLength)]
				self._overlayColorFunction = {'function':self.useColorRandomSequence, 'sequenceLength':sequenceLength, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorRandom(self, twinkleColors:bool=False)->None:
		"""
		Sets the color sequence to generate a random RGB value every time one is needed in a function

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				self.colorSequence = PixelColors.random
				self.colorSequenceCount = random.randint(2,7)
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				self._colorFunction = {'function':self.useColorRandom}
			elif twinkleColors == True:
				self.overlayColorSequence = PixelColors.random
				self.overlayColorSequenceCount = random.randint(2,7)
				self._overlayColorFunction = {'function':self.useColorRandom, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSequenceRepeating(self, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE, twinkleColors:bool=False)->None:
		"""
		Sets the color sequence used by light functions to the sequence given, buts repeats it across the entire light string

		If the sequence will not fill perfectly when repeated, the virtual LED string is extended until it fits

		colorSequence:List[Pixel]
			list of colors to in the pattern being shifted across the LED string

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
				self.colorSequence = LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence)
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorSequenceRepeating, 'colorSequence':self.colorSequence}
			elif twinkleColors == True:
				arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
				self.overlayColorSequence = LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence)
				self._overlayColorFunction = {'function':self.useColorSequenceRepeating, 'colorSequence':self.colorSequence, 'twinkleColors':True}
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorTransition(self, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE, stepsPerTransition:int=5, wrap:bool=True, twinkleColors:bool=False)->None:
		"""
		sets the color sequence used by light functions to the one specified in the argument, but
		makes a smooth transition from one color to the next over the length specified

		colorSequence:List[Pixel]
			list of colors to transition between

		stepsPerTransition: int
			how many pixels it takes to transition from one color to the next

		wrap: bool
			if true, the last color of the sequence will transition to the first color as the final transition

		twinkleColors:bool
			set to true when assigning these colors to be used in a twinkle overlay

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				self.colorSequence = LightPattern.ColorTransitionArray(arrayLength=len(colorSequence)*int(stepsPerTransition),wrap=False, colorSequence=colorSequence)
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorTransition, 'colorSequence':self.colorSequence, 'stepsPerTransition':stepsPerTransition, 'wrap':wrap}
			elif twinkleColors == True:
				self.overlayColorSequence = LightPattern.ColorTransitionArray(arrayLength=len(colorSequence)*int(stepsPerTransition),wrap=False, colorSequence=colorSequence)
				self._overlayColorFunction = {'function':self.useColorTransition, 'colorSequence':self.colorSequence, 'stepsPerTransition':stepsPerTransition, 'wrap':wrap, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorTransitionRepeating(self, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE, stepsPerTransition:int=5, wrap:bool=True, twinkleColors:bool=False):
		"""
		colorSequence:List[Pixel]
			list of colors to in the pattern being shifted across the LED string
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if twinkleColors == False:
				colorSequence = LightPattern.ColorTransitionArray(arrayLength=(len(colorSequence)*stepsPerTransition), wrap=wrap, colorSequence=colorSequence)
				arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
				self.colorSequence = LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence)
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorTransitionRepeating, 'colorSequence':self.colorSequence, 'stepsPerTransition':stepsPerTransition, 'wrap':wrap}
			elif twinkleColors == True:
				colorSequence = LightPattern.ColorTransitionArray(arrayLength=(len(colorSequence)*stepsPerTransition), wrap=wrap, colorSequence=colorSequence)
				arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
				self.overlayColorSequence = LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence)
				self._overlayColorFunction = {'function':self.useColorTransitionRepeating, 'colorSequence':self.colorSequence, 'stepsPerTransition':stepsPerTransition, 'wrap':wrap, 'twinkleColors':True}
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorRainbow(self, rainbowPixels:int=None, twinkleColors:bool=False):
		"""
		Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

		rainbowPixels:int
			when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if rainbowPixels == None:
				rainbowPixels = random.randint(10,self._LEDCount//2)
			if twinkleColors == False:
				self.colorSequence = LightPattern.RainbowArray(arrayLength=rainbowPixels)
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorRainbow, 'rainbowPixels':rainbowPixels}
			elif twinkleColors == True:
				self.overlayColorSequence = LightPattern.RainbowArray(arrayLength=rainbowPixels)
				self._overlayColorFunction = {'function':self.useColorRainbow, 'rainbowPixels':rainbowPixels, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorRainbowRepeating(self, rainbowPixels:int=None, twinkleColors:bool=False):
		"""
		Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

		rainbowPixels:int
			when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = DEFAULT_BACKGROUND_COLOR
			if rainbowPixels == None:
				rainbowPixels = random.randint(10,self._LEDCount//2)
			if twinkleColors == False:
				# colorSequence = LightPattern.RainbowArray(arrayLength=rainbowPixels)
				arrayLength = np.ceil(self._LEDCount / rainbowPixels) * rainbowPixels
				self.colorSequence = LightPattern.RepeatingRainbowArray(arrayLength=arrayLength, segmentLength=rainbowPixels)
				if self.colorSequenceCount < self._LEDCount:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
				else:
					self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
				self._colorFunction = {'function':self.useColorRainbowRepeating, 'rainbowPixels':rainbowPixels}
			elif twinkleColors == True:
				colorSequence = LightPattern.RainbowArray(arrayLength=rainbowPixels)
				arrayLength = np.ceil(self._LEDCount / rainbowPixels) * rainbowPixels
				self.overlayColorSequence = LightPattern.RepeatingRainbowArray(arrayLength=arrayLength, segmentLength=rainbowPixels)
				self._overlayColorFunction = {'function':self.useColorRainbowRepeating, 'rainbowPixels':rainbowPixels, 'twinkleColors':True}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise



	def functionNone(self, refreshDelay:float=None):
		"""
		Set all Pixels to the same color

		refreshDelay: float
			delay between color updates
			in this function it is only relevant if there is an overlay active

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._None_Function, configurationPointer=self._None_Configuration)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _None_Configuration(self):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._SetVirtualLEDArray(LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.colorSequenceNext))
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _None_Function(self):
		"""
		"""
		try:
			pass
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionSolidColorCycle(self, refreshDelay:float=None):
		"""
		Set all LEDs to a single color at once, but cycle between entries in a list of colors

		refreshDelay: float
			delay between color updates

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) * 2
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._SolidColorCycle_Function, configurationPointer=self._SolidColorCycle_Configuration)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _SolidColorCycle_Configuration(self):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._SetVirtualLEDArray(LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.colorSequenceNext))
			if self.colorSequenceCount < 2:
				self._NextModeChange = time.time()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _SolidColorCycle_Function(self):
		"""
		"""
		try:
			self._VirtualLEDArray *= 0
			self._VirtualLEDArray += self.colorSequenceNext
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionMarquee(self, refreshDelay:float=None, shiftAmount:int=1):
		"""
		Shifts a color pattern across the LED string marquee style.
		Uses the provided sequence of colors.

		refreshDelay: float
			delay between color updates

		shiftAmount: int
			the number of pixels the marquee shifts on each update

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Marquee_Function, configurationPointer=self._Marquee_Configuration, shiftAmount=shiftAmount)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Marquee_Configuration(self, shiftAmount:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._ShiftAmount = shiftAmount
			# colorSequence = []
			self._LightDataObjects = []
			direction = [-1,1][random.randint(0,1)]
			for i in range(self.colorSequenceCount):
				marqueePixel = LightData(self.colorSequenceNext)
				marqueePixel.step = shiftAmount
				marqueePixel.direction = direction
				marqueePixel.index = i
				self._LightDataObjects.append(marqueePixel)
				# colorSequence.append(self.colorSequenceNext)
			# self._VirtualLEDArray[:self.colorSequenceCount] = np.array(colorSequence)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Marquee_Function(self):
		"""
		"""
		try:
			self._off()
			# self._VirtualLEDIndexArray = np.roll(self._VirtualLEDIndexArray, self._ShiftAmount, 0)
			for marqueePixel in self._LightDataObjects:
				marqueePixel.index = (marqueePixel.index + (marqueePixel.direction * marqueePixel.step)) % self._VirtualLEDCount
				self._VirtualLEDArray[marqueePixel.index] = marqueePixel.color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionAlternate(self, refreshDelay:float=None, shiftAmount:int=1):
		"""
		Shift a color pattern across the Pixel string marquee style and then bounce back.

		refreshDelay: float
			delay between color updates

		shiftAmount: int
			each time the pattern shifts, shift it by this many LEDs

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 35
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Alternate_Function, configurationPointer=self._Alternate_Configuration, shiftAmount=shiftAmount)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Alternate_Configuration(self, shiftAmount:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._LightDataObjects = []
			for i in range(self.colorSequenceCount):
				alternator = LightData(self.colorSequenceNext)
				alternator.index = i
				alternator.step = 1
				alternator.shiftAmount = shiftAmount
				alternator.direction = 1
				self._LightDataObjects.append(alternator)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Alternate_Function(self):
		"""
		"""
		try:
			self._off()
			for alternator in self._LightDataObjects:
				self._VirtualLEDArray[alternator.index] = alternator.color
				if alternator.index + (alternator.direction * alternator.shiftAmount) >= self._VirtualLEDCount or \
				alternator.index + (alternator.direction * alternator.shiftAmount) < 0:
					alternator.stepCounter = 0
					alternator.direction = alternator.direction * -1
				else:
					alternator.stepCounter += 1
				alternator.index += (alternator.direction * alternator.shiftAmount)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionCylon(self, refreshDelay:float=None, fadeAmount:int=45):
		"""
		Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

		refreshDelay: float
			delay between color updates

		fadeAmount: int
			how much each pixel fades per refresh
			smaller numbers = larger tails on the cylon eye fade

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 10
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Cylon_Function, configurationPointer=self._Cylon_Configuration, fadeAmount=fadeAmount)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cylon_Configuration(self, fadeAmount:int):
		"""
		"""
		try:
			LOGGER.log(5,'%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._LightDataObjects = []
			for index in range(self.colorSequenceCount):
				color = self.colorSequenceNext
				eye = LightData(color)
				eye.index = index
				eye.step = 3
				eye.direction=1
				eye.fadeAmount = fadeAmount
				self._LightDataObjects.append(eye)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cylon_Function(self):
		"""
		"""
		try:
			self._FadeOff(fadeAmount=self._LightDataObjects[0].fadeAmount)
			for eye in self._LightDataObjects:
				last_index = eye.index
				next_index = eye.index + (eye.direction * eye.step)
				if next_index >= self._VirtualLEDCount:
					next_index = self._VirtualLEDCount-1
					eye.direction = -1
				elif next_index < 0:
					next_index = 1
					eye.direction = 1
				eye.index = next_index
				for i in np.linspace(last_index, next_index, abs(last_index - next_index)+1, dtype=int):
					self._VirtualLEDArray[i] = eye.color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionMerge(self, refreshDelay:float=None, mergeSegmentLength:int=None):
		"""
		Reflect a color sequence and shift the reflections toward each other in the middle

		refreshDelay: float
			delay between color updates

		mergeSegmentLength: int
			length of reflected segments

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 3
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Merge_Function, configurationPointer=self._Merge_Configuration, mergeSegmentLength=mergeSegmentLength)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Merge_Configuration(self, mergeSegmentLength:int):
		"""
		splits the array into sections and shifts each section in the opposite direction

		mergeSegmentLength: int
			the length of the segments to split the array into
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if mergeSegmentLength is None:
				if not self.__colorSequenceCount is None:
					mergeSegmentLength = self.__colorSequenceCount
				else:
					mergeSegmentLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
			self._MergeLength = int(mergeSegmentLength)
			arrayLength = np.ceil(self._LEDCount / self._MergeLength) * self._MergeLength
			colorSequence = []
			if self.colorSequenceCount >= self._LEDCount:
				self.colorSequenceCount = self.colorSequenceCount //2
			for i in range(self.colorSequenceCount):
				colorSequence.append(self.colorSequenceNext)
			self._SetVirtualLEDArray(LightPattern.ReflectArray(arrayLength=arrayLength, colorSequence=colorSequence, foldLength=self.colorSequenceCount))
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Merge_Function(self):
		"""
		"""
		try:
			# this takes
			# [0,1,2,3,4,5]
			# and creates
			# [[0,1,2]
			#  [3,4,5]]
			# out of it
			segmentCount = int(self._VirtualLEDIndexCount // self._MergeLength)
			temp = np.reshape(self._VirtualLEDIndexArray, (segmentCount, self._MergeLength))
			# now i can roll each row in a different direction and then undo
			# the matrixification of the array
			for i in range(self._VirtualLEDIndexCount // self._MergeLength):
				if i % 2 == 0:
					temp[i] = np.roll(temp[i], 1, 0)
				else:
					temp[i] = np.roll(temp[i], -1, 0)
			# turn the matrix back into an array
			temp = np.reshape(temp, (self._VirtualLEDIndexCount))
			for i in range(len(temp)):
				self._VirtualLEDIndexArray[i] = temp[i]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionAccelerate(self, beginDelay:float=None, endDelay:float=None):
		"""
		Shifts a color pattern across the LED string marquee style, but accelerates as it goes.
		Uses the provided sequence of colors.

		beginDelay: float
			initial delay between color updates
		endDelay: float
			final delay between color updates
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if beginDelay is None:
				beginDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
			if endDelay is None:
				endDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 10000
			self._initializeFunction(refreshDelay=beginDelay, functionPointer=self._Accelerate_Function, configurationPointer=self._Accelerate_Configuration, shiftAmount=1, beginDelay=beginDelay, endDelay=endDelay)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Accelerate_Configuration(self, shiftAmount:int, beginDelay:float, endDelay:float):
		"""
		incrementally decreases the amount of self.refreshDelay between each shift
		for 'delaySteps' then maintains 'endDelay'

		shiftAmount: int
			the amount to shift each time

		beginDelay: float
			the number of seconds to delay at the beginning

		endDelay: float
			the number of seconds to delay at the end
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			delaySteps = self._VirtualLEDCount //2
			self._ShiftAmount=1
			self._BeginDelay=beginDelay
			self._EndDelay=endDelay
			self._DelaySteps=delaySteps
			self._DelayRange = np.log(np.linspace(np.e, 1, self._DelaySteps)) * (self._BeginDelay - self._EndDelay) + self._EndDelay
			if self._DelaySteps < self._VirtualLEDIndexCount:
				self._DelayRange = np.concatenate((self._DelayRange, np.ones(self._VirtualLEDIndexCount - self._DelaySteps) * self._EndDelay))
			self._AccelerateIndex = 0
			self._AccelerateDirection = 1
			self._LightDataObjects = []
			direction = [-1,1][random.randint(0,1)]
			for i in range(self.colorSequenceCount):
				marqueePixel = LightData(self.colorSequenceNext)
				marqueePixel.step = shiftAmount
				marqueePixel.direction = direction
				marqueePixel.index = i
				self._LightDataObjects.append(marqueePixel)
			# self._FunctionList.append(self._Accelerate_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Accelerate_Function(self):
		"""
		"""
		try:
			self._off()
			for marqueePixel in self._LightDataObjects:
				if (self._AccelerateIndex / self._DelaySteps) >= 0.8:
					marqueePixel.step = 3
				elif (self._AccelerateIndex / self._DelaySteps) >= 0.6:
					marqueePixel.step = 2
				else:
					marqueePixel.step = 1

				marqueePixel.index = (marqueePixel.index + (marqueePixel.direction * marqueePixel.step)) % self._VirtualLEDCount
				self._VirtualLEDArray[marqueePixel.index] = marqueePixel.color
			if self._AccelerateDirection > 0:
				self._AccelerateIndex += 1
			else:
				self._AccelerateIndex -= 1

			if self._AccelerateIndex >= (len(self._DelayRange)-1) or \
				self._AccelerateIndex <= 0:
				if self._AccelerateDirection < 0 and random.randint(0,10) > 8:
					self._ShiftAmount *= -1
				self._AccelerateDirection *= -1
			self.refreshDelay = self._DelayRange[self._AccelerateIndex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionRandomChange(self, refreshDelay:float=None, changeChance:float=0.01):
		"""
		Randomly changes pixels on the string to one of the provided colors

		refreshDelay: float
			delay between color updates

		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._RandomChange_Function, configurationPointer=self._RandomChange_Configuration, changeChance=changeChance)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChange_Configuration(self, changeChance:float):
		"""

		changeChance: float
			a floating point number specifying the chance of
			modifying any given LED's value
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._RandomChangeChance = changeChance
			if self.colorSequenceCount < 2:
				self._NextModeChange = time.time()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChange_Function(self):
		"""
		"""
		try:
			maxVal = 1000
			for LEDIndex in range(self._VirtualLEDIndexCount):
				doLight = random.randint(0, maxVal)
				if doLight > maxVal * (1.0 - self._RandomChangeChance):
					self._VirtualLEDArray[LEDIndex] = self.colorSequenceNext
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionRandomFadeChange(self, refreshDelay:float=None, changeChance:float=0.2, fadeStepCount:int=50):
		"""
		Randomly changes pixels on the string to one of the provided colors by fading from one color to the next

		refreshDelay: float
			delay between color updates

		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)

		fadeStepCount: int
			number of steps in the transition from one color to the next

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._RandomFadeChange_Function, configurationPointer=self._RandomFadeChange_Configuration, fadeInChance=changeChance, fadeStepCount=fadeStepCount)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomFadeChange_Configuration(self, fadeInChance:float, fadeStepCount:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeChance = fadeInChance
			self._FadeStepCount = fadeStepCount
			self._FadeAmount = 255 // self._FadeStepCount
			self._FadeStepCounter = 0
			self._PreviousIndices = []
			indices = self._GetRandomIndices(self._FadeChance)
			self._LightDataObjects = []
			for index in indices:
				self._PreviousIndices.append(index)
				randomfade = LightData(self.colorSequenceNext)
				randomfade.index = index
				randomfade.fadeAmount = self._FadeAmount
				randomfade.stepCountMax = self._FadeStepCount
				self._LightDataObjects.append(randomfade)
			self._PreviousIndices = np.array(self._PreviousIndices)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomFadeChange_Function(self):
		"""
		"""
		try:
			for randomFade in self._LightDataObjects:
				self._FadeLED(led_index=randomFade.index, offColor=randomFade.color, fadeAmount=randomFade.fadeAmount)
				randomFade.stepCounter += 1
				if randomFade.stepCounter >= randomFade.stepCountMax:
					randomFadeIndices = np.array(self._GetRandomIndices(self._FadeChance))
					x = np.intersect1d(self._PreviousIndices, randomFadeIndices)
					randomFadeIndices = [i for i in randomFadeIndices if not i in x]
					defaultIndices = np.array(self._GetRandomIndices(self._FadeChance))
					x = np.intersect1d(self._PreviousIndices, defaultIndices)
					defaultIndices = [i for i in defaultIndices if not i in x]
					x = np.intersect1d(randomFadeIndices, defaultIndices)
					defaultIndices = [i for i in defaultIndices if not i in x]
					self._PreviousIndices = []
					self._LightDataObjects = []
					for index in randomFadeIndices:
						if index < self._VirtualLEDCount:
							self._PreviousIndices.append(index)
							randomfade = LightData(self.colorSequenceNext)
							randomfade.index = index
							randomfade.fadeAmount = self._FadeAmount
							randomfade.stepCountMax = self._FadeStepCount
							self._LightDataObjects.append(randomfade)
					for index in defaultIndices:
						if index < self._VirtualLEDCount:
							randomfade = LightData(self.backgroundColor)
							randomfade.index = index
							randomfade.fadeAmount = self._FadeAmount
							randomfade.stepCountMax = self._FadeStepCount
							self._LightDataObjects.append(randomfade)
					self._PreviousIndices = np.array(self._PreviousIndices)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionMeteors(self, refreshDelay:float=None, fadeStepCount:int=5, maxSpeed:int=2):
		"""
		creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail

		refreshDelay: float
			delay between color updates

		fadeStepCount: int
			this is the length of the meteor trail

		maxSpeed: int
			the amount be which the meteor moves each refresh

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Meteors_Function, configurationPointer=self._Meteors_Configuration, fadeStepCount=fadeStepCount, maxSpeed=maxSpeed)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Configuration(self, fadeStepCount:int, maxSpeed:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._LightDataObjects = []
			rnge = [i for i in range(-maxSpeed,maxSpeed+1)]
			for index in range(min(self.colorSequenceCount, 4)):
				meteor = LightData(self.colorSequenceNext)
				meteor.index = random.randint(0,self._VirtualLEDIndexCount-1)
				meteor.fadeAmount = np.ceil(255/fadeStepCount)
				meteor.step = rnge[random.randint(0,len(rnge)-1)]
				while meteor.step == 0:
					meteor.step = rnge[random.randint(0,len(rnge)-1)]
				meteor.stepCountMax = random.randint(2, self._VirtualLEDIndexCount-1)
				self._LightDataObjects.append(meteor)
			self._FadeAmount = int(255 / fadeStepCount)
			self._MaxSpeed = maxSpeed
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Function(self):
		"""
		"""
		try:
			rnge = [i for i in range(-self._MaxSpeed,self._MaxSpeed+1)]
			self._FadeOff(fadeAmount=self._LightDataObjects[0].fadeAmount)
			for meteor in self._LightDataObjects:
				oldLocation = meteor.index
				newLocationx = (meteor.index + meteor.step)
				newLocation = (meteor.index + meteor.step) % self._VirtualLEDIndexCount
				meteor.index = newLocation
				meteor.stepCounter += 1
				if meteor.stepCounter >= meteor.stepCountMax:
					meteor.stepCounter = 0
					meteor.step = rnge[random.randint(0,len(rnge)-1)]
					while meteor.step == 0:
						meteor.step = rnge[random.randint(0,len(rnge)-1)]
					meteor.stepCountMax = random.randint(2,self._VirtualLEDIndexCount*2)
					meteor.color = self.colorSequenceNext
					meteor.index = random.randint(0,self._VirtualLEDIndexCount-1)
				# rng = []
				# if newLocation > oldLocation:
				rng = range(oldLocation, newLocationx + 1)
				if len(rng) > 5:
					print('hey')
				# else:
					# newLocation = (newLocation - 1)% self._VirtualLEDCount
				for i in rng:
					i = i% self._VirtualLEDCount
					self._VirtualLEDArray[i] = meteor.color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionMeteorsFancy(self, refreshDelay:float=None, fadeAmount:int=75, maxSpeed:int=2, cycleColors:bool=False, meteorCount:int=3):
		"""
		Creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail.
		In this version each meteor contains all colors of the colorSequence.

		refreshDelay: float
			delay between color updates

		fadeAmount: int
			the amount by which meteors are faded

		maxSpeed: int
			the amount be which the meteor moves each refresh

		cycleColors: bool
			if True, the meteors transition through the color sequence as they travel

		meteorCount: int
			the number of meteors flying around

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._MeteorsFancy_Function, configurationPointer=self._MeteorsFancy_Configuration, meteorCount=meteorCount, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors, randomColorCount=None)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsFancy_Configuration(self, meteorCount:int, maxSpeed:int, fadeAmount:int, cycleColors:bool, randomColorCount:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._MeteorCount = meteorCount
			self._FadeAmount = fadeAmount
			self._CycleColors = cycleColors
			self._MaxSpeed = maxSpeed
			for i in range(self._MeteorCount):
				colorSequence = LightPattern.ConvertPixelArrayToNumpyArray([self.colorSequenceNext for i in range(self.colorSequenceCount)])
				meteor = LightData(colorSequence[::-1])
				meteor.index = random.randint(0,self._VirtualLEDCount-1)
				meteor.step = (-maxSpeed, maxSpeed)[random.randint(0,1)]
				meteor.stepCountMax = random.randint(2, self._VirtualLEDCount*2)
				self._LightDataObjects.append(meteor)
			# self._FunctionList.append(self._MeteorsFancy_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsFancy_Function(self):
		"""
		"""
		try:
			self._FadeOff()
			for meteor in self._LightDataObjects:
				oldIndex = meteor.index
				newIndex = (meteor.index + meteor.step)
				meteor.index = (meteor.index + meteor.step) % self._VirtualLEDCount
				meteor.stepCounter += 1
				if meteor.stepCounter >= meteor.stepCountMax:
					meteor.stepCounter = 0
					meteor.step = (-self._MaxSpeed, self._MaxSpeed)[random.randint(0,1)]
					meteor.stepCountMax = random.randint(2,self._VirtualLEDCount*2)
					colorSequence = LightPattern.ConvertPixelArrayToNumpyArray([self.colorSequenceNext for i in range(self.colorSequenceCount)])
					meteor.colors = colorSequence[::-1]
				if not self._CycleColors:
					for i in range(0,len(meteor.colors)):
						self._VirtualLEDArray[(meteor.index + meteor.step * i) % self._VirtualLEDCount] = meteor.colors[i]
				else:
					for i in range(0,len(meteor.color)):
						self._VirtualLEDArray[(meteor.index + meteor.step * i) % self._VirtualLEDCount] = meteor.colors[(meteor.colorIndex + i) % len(meteor.colors)]
				if self._CycleColors:
					meteor.colorIndex = (meteor.colorIndex + 1) % len(meteor.colors)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionMeteorsBouncy(self, refreshDelay:float=None, fadeAmount:int=80, maxSpeed:int=1, explode:bool=True):
		"""
		Creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail.
		In this version each meteor contains all colors of the colorSequence.

		refreshDelay: float
			delay between color updates

		fadeAmount: int
			the amount by which meteors are faded

		maxSpeed: int
			the amount be which the meteor moves each refresh

		explode: bool
			if True, the meteors will light up in an explosion when they collide

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 10
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._MeteorsBouncy_Function, configurationPointer=self._MeteorsBouncy_Configuration, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsBouncy_Configuration(self, fadeAmount:int, maxSpeed:int, explode:bool):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeAmount = fadeAmount
			# self._MaxSpeed = maxSpeed
			self._Explode = explode
			otherSpeeds = []
			self._LightDataObjects = []
			for index in range(max(min(self.colorSequenceCount, 4),2)):
				meteor = LightData(self.colorSequenceNext)
				meteor.index = random.randint(0, self._VirtualLEDCount -1)
				meteor.previousIndex = meteor.index
				meteor.step = (-maxSpeed, maxSpeed)[random.randint(0,1)]
				while abs(meteor.step) in otherSpeeds:
					if meteor.step > 0:
						meteor.step += 1
					else:
						meteor.step -= 1
				otherSpeeds.append(abs(meteor.step))
				self._LightDataObjects.append(meteor)
			# make sure there are at least two going to collide
			if self._LightDataObjects[0].step * self._LightDataObjects[1].step > 0:
				self._LightDataObjects[1].step *= -1
			# self._FunctionList.append(self._MeteorsBouncy_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsBouncy_Function(self):
		"""
		"""
		try:
			self._FadeOff()
			# move the meteors
			for meteor in self._LightDataObjects:
				# calculate next index
				oldIndex = meteor.index
				newIndex = (meteor.index + meteor.step)
				newLocation = (meteor.index + meteor.step) % self._VirtualLEDCount
				# save previous index
				meteor.previousIndex = meteor.index
				# assign new index
				meteor.index = newLocation
				# positive step
				if meteor.previousIndex < meteor.index:
					# wrap around LED string
					if abs(meteor.previousIndex - meteor.index) > abs(meteor.step)+1:
						meteor.moveRange = [r % self._VirtualLEDCount for r in range(meteor.index, meteor.previousIndex+self._VirtualLEDCount+1)]
					# not wrapping around
					else:
						meteor.moveRange = range(meteor.previousIndex, meteor.index+1)
				# negative step
				else:
					# wrap around LED string
					if abs(meteor.previousIndex - meteor.index) > abs(meteor.step)+1:
						meteor.moveRange = [r % self._VirtualLEDCount for r in range(meteor.previousIndex, meteor.index+self._VirtualLEDCount+1)]
					# not wraping around
					else:
						meteor.moveRange = range(meteor.index, meteor.previousIndex+1)
				if meteor.index > self._VirtualLEDCount:
					meteor.index = self._VirtualLEDCount
			# detect collision of self._LightDataObjects
			foundBounce = False
			if len(self._LightDataObjects) > 1:
				for index1, meteor1 in enumerate(self._LightDataObjects):
					if index1 + 1 < len(self._LightDataObjects):
						for index2, meteor2 in enumerate(self._LightDataObjects[index1+1:]):
							# this detects the intersection of two self._LightDataObjects' movements across LEDs
							if len(list(set(meteor1.moveRange) & set(meteor2.moveRange))) > 0 and random.randint(0,1000) > 200:
								meteor1.bounce = meteor2
								meteor1.oldStep = meteor1.step
								meteor2.bounce = meteor1
								meteor2.oldStep = meteor2.step
								foundBounce = True
			# handle collision of self._LightDataObjects
			explosions=[]
			if foundBounce == True:
				for index, meteor in enumerate(self._LightDataObjects):
					if meteor.bounce:
						previous = int(meteor.step)
						meteor.step = meteor.bounce.oldStep * -1
						newLocation = (meteor.index + meteor.step) % self._VirtualLEDCount
						meteor.index = newLocation + random.randint(0,3)
						meteor.previousIndex = newLocation
						if random.randint(0,1000) > 800:
							meteor.color = self.colorSequenceNext
						meteor.bounce = False
						if self._Explode:
							middle = meteor.moveRange[len(meteor.moveRange)//2]
							r = (self._LEDCount//20)
							for i in range(r):
								explosions.append(((middle-i) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).array * (r-i)/r))
								explosions.append(((middle+i) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).array * (r-i)/r))
								# explosions.append(((middle-5) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).array))
								# explosions.append(((middle-4) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
								# explosions.append(((middle-3) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
								# explosions.append(((middle-2) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
								# explosions.append(((middle-1) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
								# explosions.append(((middle+1) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
								# explosions.append(((middle+2) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
								# explosions.append(((middle+3) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
								# explosions.append(((middle+4) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
								# explosions.append(((middle+5) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).array))
								# explosions.append(((middle+6) % self._VirtualLEDCount, Pixel(PixelColors.GRAY).array))
			for index, meteor in enumerate(self._LightDataObjects):
				try:
					if meteor.index > self._VirtualLEDCount-1:
						meteor.index = meteor.index % (self._VirtualLEDCount)
					for i in meteor.moveRange:
						self._VirtualLEDArray[i] = meteor.color
				except:
					# LOGGER.exception('len(self._LightDataObjects)={},len(meteor[{}]={}, itms[{},{}] len(LEDS)={}'.format(len(self._LightDataObjects), led, len(self._LightDataObjects[led]), index, color, len(self._VirtualLEDArray)))
					raise
			if self._Explode and len(explosions) > 0:
				for x in explosions:
					self._VirtualLEDArray[x[0]] = x[1]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionMeteorsAgain(self, refreshDelay:float=None, maxDelay:int=5, fadeSteps:int=10):
		"""
		refreshDelay: float
			delay between color updates
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 1000
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._MeteorsAgain_Function, configurationPointer=self._MeteorsAgain_Configuration, maxDelay=maxDelay, fadeSteps=fadeSteps)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsAgain_Configuration(self, maxDelay:int, fadeSteps:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._MaxDelay = maxDelay
			self._FadeSteps = fadeSteps
			self._FadeAmount = np.ceil(255/fadeSteps)
			self._LightDataObjects = []
			for index in range(max(min(self.colorSequenceCount, 5), 2)):
				meteor = LightData(self.colorSequenceNext)
				meteor.index = random.randint(0, self._VirtualLEDCount-1)
				meteor.direction = (-1,1)[random.randint(0, 1)]
				meteor.step = (-1,1)[random.randint(0, 1)]
				meteor.delayCountMax = random.randint(0, maxDelay)
				meteor.stepCountMax = random.randint(2, self._VirtualLEDCount*6)
				meteor.colorSequenceIndex = index
				self._LightDataObjects.append(meteor)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsAgain_Function(self):
		"""
		"""
		try:
			for meteor in self._LightDataObjects:
				meteor.delayCounter += 1
				if meteor.delayCounter >= meteor.delayCountMax:
					meteor.delayCounter = 0
					newLocation = (meteor.index + meteor.step) % self._VirtualLEDCount
					meteor.index = newLocation
					meteor.stepCounter += 1
					if meteor.stepCounter >= meteor.stepCountMax:
						meteor.stepCounter = 0
						meteor.step = (-1,1)[random.randint(0,1)]
						meteor.delayCountMax = random.randint(0, self._MaxDelay)
						meteor.stepCountMax = random.randint(self._VirtualLEDCount,self._VirtualLEDCount*4)
			self._FadeOff()
			for meteor in self._LightDataObjects:
				self._VirtualLEDArray[meteor.index] = meteor.color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionPaint(self, refreshDelay:float=None, maxDelay:int=5):
		"""
		wipes colors in the current sequence across the pixel strand in random directions and amounts

		refreshDelay: float
			delay between color updates

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 1000
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Paint_Function, configurationPointer=self._Paint_Configuration, maxDelay=maxDelay)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Paint_Configuration(self, maxDelay:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._MaxDelay = maxDelay
			self._LightDataObjects = []
			for i in range(max(min(self.colorSequenceCount, 10), 2)):
				paintBrush = LightData(self.colorSequenceNext)
				paintBrush.index = random.randint(0, self._VirtualLEDCount-1)
				paintBrush.step = (-1, 1)[random.randint(0,1)]
				paintBrush.delayCountMax = random.randint(min(0, self._MaxDelay), max(0, self._MaxDelay))
				paintBrush.stepCountMax = random.randint(2, self._VirtualLEDCount*2)
				paintBrush.colorSequenceIndex = i
				self._LightDataObjects.append(paintBrush)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Paint_Function(self):
		"""
		"""
		try:
			for paintBrush in self._LightDataObjects:
				paintBrush.delayCounter += 1
				if paintBrush.delayCounter >= paintBrush.delayCountMax:
					paintBrush.delayCounter = 0
					newLocation = (paintBrush.index + paintBrush.step) % self._VirtualLEDCount
					paintBrush.index = newLocation
					paintBrush.stepCounter += 1
					if paintBrush.stepCounter >= paintBrush.stepCountMax:
						paintBrush.stepCounter = 0
						paintBrush.step = (-1, 1)[random.randint(-1,1)]
						paintBrush.delayCountMax = random.randint(0, self._MaxDelay)
						paintBrush.stepCountMax = random.randint(2, self._VirtualLEDCount*2)
						if paintBrush.random:
							paintBrush.color = self.colorSequenceNext
				self._VirtualLEDArray[paintBrush.index] = paintBrush.color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionSprites(self, refreshDelay:float=None, fadeSteps:int=3):
		"""
		Uses colors in the current list to fly meteor style across
		the pixel strand in short bursts of random length and direction.

		refreshDelay: float
			delay between color updates
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Sprites_Function, configurationPointer=self._Sprites_Configuration, fadeSteps=fadeSteps)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Sprites_Configuration(self, fadeSteps:int):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeSteps = fadeSteps
			self._FadeAmount = np.ceil(255/fadeSteps)
			self._LightDataObjects = []
			for i in range(max(min(self.colorSequenceCount, 10),2)):
				sprite = LightData(self.colorSequenceNext)
				sprite.active = False
				sprite.index = random.randint(0, self._VirtualLEDCount-1)
				sprite.lastindex = sprite.index
				sprite.direction = [-1,1][random.randint(0,1)]
				sprite.colorSequenceIndex = i
				# sprite.random = randomColors
				self._LightDataObjects.append(sprite)
			self._LightDataObjects[0].active = True
			# self._FunctionList.append(self._Sprites_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Sprites_Function(self):
		"""
		"""
		try:
			self._FadeOff()
			for sprite in self._LightDataObjects:
				if sprite.active:
					still_alive = random.randint(6,self._VirtualLEDCount//2) > sprite.duration
					if still_alive:
						sprite.lastindex = sprite.index
						step_size = random.randint(1,3)*sprite.direction
						#sprite[sprite_direction] = step_size * 2
						mi = min(sprite.index, sprite.index + step_size)
						ma = max(sprite.index, sprite.index + step_size)
						first = True
						if sprite.direction > 0:
							for index in range(mi+1, ma+1):
								index = index % self._VirtualLEDCount
								sprite.index = index
								self._VirtualLEDArray[sprite.index] = sprite.color
								if not first:
									self._FadeLED(index, self.backgroundColor, self._FadeAmount)
								first - False
							#sprite[sprite_index] = ma
						else:
							for index in range(ma-1, mi-1,-1):
								index = index % self._VirtualLEDCount
								sprite.index = index
								self._VirtualLEDArray[sprite.index] = sprite.color
								if not first:
									self._FadeLED(index, self.backgroundColor, self._FadeAmount)
								first - False
							#sprite[sprite_index] = mi
						sprite.duration += 1
					else:
						sprite.active = False
				else:
					if random.randint(0,999) > 800:
						next_sprite = random.randint(0, (len(self._LightDataObjects) - 1))
						sprite = self._LightDataObjects[next_sprite]
						sprite.active = True
						sprite.duration = 0
						sprite.direction = [-1,1][random.randint(0,1)]
						sprite.index = random.randint(0, self._VirtualLEDCount-1)
						sprite.lastindex = sprite.index
						# if sprite.random:
						sprite.color = self.colorSequenceNext
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def functionRaindrops(self, refreshDelay:float=None, maxSize:int=10, fadeAmount:int=5, raindropChance:float=0.05):
		"""
		Uses colors in the current list to cause random "splats" across the led strand
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Raindrops_Function, configurationPointer=self._Raindrops_Configuration, fadeAmount=fadeAmount, maxSize=maxSize, raindropChance=raindropChance)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Raindrops_Configuration(self, fadeAmount:int, maxSize:int, raindropChance:float):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeAmount = fadeAmount
			self._LightDataObjects = []
			for i in range(max(min(self.colorSequenceCount, 10), 2)):
				raindrop = LightData(self.colorSequenceNext)
				raindrop.maxSize = maxSize
				raindrop.index = random.randint(0, self._VirtualLEDCount-1)
				raindrop.stepCountMax = random.randint(2, raindrop.maxSize)
				raindrop.fadeAmount = ((255/raindrop.stepCountMax)/255)*2
				raindrop.active = False
				raindrop.activeChance = raindropChance
				self._LightDataObjects.append(raindrop)
			self._LightDataObjects[0].active = True
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Raindrops_Function(self):
		"""
		"""
		try:
			self._FadeOff()
			for raindrop in self._LightDataObjects:
				if not raindrop.active:
					chance = random.randint(0, 1000) / 1000
					if chance < raindrop.activeChance:
						raindrop.active = True
				if raindrop.active:
					if raindrop.stepCounter < raindrop.stepCountMax:
						self._VirtualLEDArray[(raindrop.index + raindrop.stepCounter) % self._VirtualLEDCount] = raindrop.color
						self._VirtualLEDArray[(raindrop.index - raindrop.stepCounter) % self._VirtualLEDCount] = raindrop.color
						raindrop.color[:] = raindrop.color * ((raindrop.stepCountMax - raindrop.stepCounter) / raindrop.stepCountMax)
						p = Pixel(raindrop.color)
						raindrop.stepCounter += 1
					else:
						raindrop.index = random.randint(0, self._VirtualLEDCount-1)
						raindrop.stepCountMax = random.randint(2, raindrop.maxSize)
						raindrop.fadeAmount = ((255/raindrop.stepCountMax)/255)*2
						raindrop.stepCounter = 0
						raindrop.color = self.colorSequenceNext.copy()
						raindrop.active = False
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionTwinkle(self, refreshDelay:float=None, twinkleChance:float=0.025):
		"""
		Randomly sets some lights to 'twinkleColor' temporarily

		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 10
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._None_Function, configurationPointer=self._None_Configuration)
			self._initializeOverlay(functionPointer=self._Twinkle_Overlay, configurationPointer=self._Twinkle_Configuration, twinkleChance=twinkleChance)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Twinkle_Configuration(self, twinkleChance:float):
		"""
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._TwinkleChance = float(twinkleChance)
			self._overlayColorFunction = {k:v for k,v in self._colorFunction.items()}
			self._overlayColorFunction['twinkleColors'] = True
			self.useColorSingle(PixelColors.OFF)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Twinkle_Overlay(self):
		"""
		"""
		try:
			maxVal = 1000
			if self._TwinkleChance > 0.0:
				for LEDIndex in range(self._LEDCount):
					doLight = random.randint(0,maxVal)
					if doLight > maxVal * (1.0 - self._TwinkleChance):
						self._LEDArray[LEDIndex] = self.overlayColorSequenceNext
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def functionBlink(self, refreshDelay:float=None, blinkChance:float=0.02):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if refreshDelay is None:
				refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._None_Function, configurationPointer=self._None_Configuration)
			self._initializeOverlay(functionPointer=self._Blink_Overlay, configurationPointer=self._Blink_Configuration, blinkChance=blinkChance)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Blink_Configuration(self, blinkChance:float):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._BlinkChance = float(blinkChance)
			self._overlayColorFunction = {k:v for k,v in self._colorFunction.items()}
			self._overlayColorFunction['twinkleColors'] = True
			self.useColorSingle(PixelColors.OFF)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Blink_Overlay(self):
		"""
		Randomly sets some lights to 'twinkleColor' without changing
		the _VirtualLEDArray buffer

		Parameters:
			twinkleChance: float
				chance of of any LED being set to 'twinkleColor'

			twinkleColor: tuple(int,int,int)
				the RGB color tuple to be used as the twinkle color
		"""
		try:
			self._Blink = not self._Blink
			if self._Blink and self._BlinkChance > 0.0:
				for i in range(self.overlayColorSequenceCount):
					color = self.overlayColorSequenceNext
					maxVal = 1000
					doBlink = random.randint(0, maxVal)
					if doBlink > maxVal * (1.0 - self._BlinkChance):
						for LEDIndex in range(self._LEDCount):
						# for rgbIndex in range(len(color)):
							# self._LEDArray[:,rgbIndex] *= 0
							# self._LEDArray[:,rgbIndex] += color[rgbIndex]
							self._LEDArray[LEDIndex] = color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def demo(self, secondsPerMode=20):
		try:
			self.secondsPerMode = secondsPerMode
			# omitted = [LightFunction.Do_Spaz.__name__, LightFunction.Do_SolidColor_SinglePseudoRandomColor.__name__, LightFunction.Do_SolidColor_SinglePseudoRandomColor.__name__, LightFunction.Do_SolidColor_SingleRandomColor.__name__]
			omitted = [LightFunction.functionNone.__name__, LightFunction.useColorSingle.__name__, LightFunction.useColorSinglePseudoRandom.__name__, LightFunction.useColorSingleRandom.__name__, LightFunction.functionBlink.__name__]
			attrs = list(dir(self))
			attrs = [a for a in attrs if not a in omitted]
			funcs = [f for f in attrs if f[:8] == 'function']
			colors = [c for c in attrs if c[:8] == 'useColor']
			funcs.sort()
			colors.sort()
			while True:
				funcs_copy = funcs.copy()
				colors_copy = colors.copy()
				try:
					while len(funcs_copy) > 0 and len(colors_copy) > 0:
						self.reset()
						clr = colors_copy[random.randint(0, len(colors)-1)]
						colors_copy.remove(clr)
						getattr(self, clr)()
						fnc = funcs_copy[random.randint(0, len(funcs)-1)]
						funcs_copy.remove(fnc)
						getattr(self, fnc)()
						c = self._colorFunction.copy()
						c.pop('function')
						self._colorFunction['function'](**c)
						self.run()
				except Exception as ex:
					LOGGER.exception(ex)
		except SystemExit:
			pass
		except KeyboardInterrupt:
			pass
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def test(self, secondsPerMode=0.5, function_names=[], color_names=[], skip_functions=[], skip_colors=[]):
		try:
			self.secondsPerMode = secondsPerMode
			attrs = list(dir(self))
			funcs = [f for f in attrs if f[:8] == 'function']
			colors = [c for c in attrs if c[:8] == 'useColor']
			funcs.sort()
			colors.sort()
			if len(function_names) > 0:
				matches = []
				for name in function_names:
					matches.extend([f for f in funcs if name.lower() in f.lower()])
				funcs = matches
			if len(color_names) > 0:
				matches = []
				for name in color_names:
					matches.extend([f for f in colors if name.lower() in f.lower()])
				colors = matches
			if len(skip_functions) > 0:
				matches = []
				for name in skip_functions:
					for f in funcs:
						if name.lower() in f.lower():
							funcs.remove(f)
			if len(skip_colors) > 0:
				matches = []
				for name in skip_colors:
					for f in colors :
						if name.lower() in f.lower():
							colors.remove(f)
			for f in funcs:
				for c in colors:
					self.reset()
					getattr(self, c)()
					getattr(self, f)()
					self.run()
		except SystemExit:
			pass
		except KeyboardInterrupt:
			pass
		except Exception as ex:
			LOGGER.exception('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

