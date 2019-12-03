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

class LightFunction:
	"""
	"""
	def __init__(self, ledCount, pwmGPIOpin, channelDMA, frequencyPWM, invertSignalPWM=False, ledBrightnessFloat=1, channelPWM=0, stripTypeLED=None, gamma=None, debug:bool=False, verbose:bool=False):
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

			self.__refreshDelay = 0.001
			self.__secondsPerMode = 120
			self.__backgroundColor = PixelColors.OFF
			self.__colorSequence = LightPattern.ConvertPixelArrayToNumpyArray([])
			self.__colorSequenceCount = 0
			self.__colorSequenceIndex = 0

			self._LoopForever = False
			self._OverlayList = []
			self._TwinkleChance = 0.0
			self._TwinkleColorList = [PixelColors.WHITE]
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			temp = self.colorSequence.array
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
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RunConfigurations(self):
		try:
			for function in self._FunctionList:
				function[1](*function[2], **function[3])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RunOverlays(self):
		try:
			for overlay in self._OverlayList:
				overlay()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
					LOGGER.error('_Run Loop Error: {}'.format(ex))
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise



	def useColorSingle(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, foregroundColor:Pixel=DEFAULT_COLOR_SEQUENCE[0]):
		"""

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor
			self.colorSequence = LightPattern.ConvertPixelArrayToNumpyArray([foregroundColor])
			self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			self._colorFunction = {'function':self.useColorSingle, 'backgroundColor':self.backgroundColor, 'foregroundColor':self.colorSequence[0]}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSinglePseudoRandom(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR):
		"""

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor
			self.colorSequence = [PixelColors.pseudoRandom()]
			self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			self._colorFunction = {'function':self.useColorSinglePseudoRandom, 'backgroundColor':self.backgroundColor}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSingleRandom(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR):
		"""

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor
			self.colorSequence = [PixelColors.random()]
			self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			self._colorFunction = {'function':self.useColorSingleRandom, 'backgroundColor':self.backgroundColor}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSequence(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE):
		"""

		backgroundColor:Pixel
			color to set any LED that isn't part of the pattern
		colorSequence:List[Pixel]
			list of colors to in the pattern being shifted across the LED string
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor
			self.colorSequence = colorSequence
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorSequence, 'backgroundColor':self.backgroundColor, 'colorSequence':self.colorSequence}
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorPseudoRandomSequence(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, sequenceLength:int=None):
		"""

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if sequenceLength is None:
				sequenceLength = random.randint(self._LEDCount//20, self._LEDCount //10)
			self.backgroundColor = backgroundColor=PixelColors.OFF
			self.colorSequence = [PixelColors.pseudoRandom() for i in range(sequenceLength)]
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorPseudoRandomSequence, 'backgroundColor':self.backgroundColor, 'sequenceLength':sequenceLength}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorRandomSequence(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, sequenceLength:int=None):
		"""

		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if sequenceLength is None:
				sequenceLength = random.randint(self._LEDCount//20, self._LEDCount //10)
			self.backgroundColor = backgroundColor=PixelColors.OFF
			self.colorSequence = [PixelColors.random() for i in range(sequenceLength)]
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorRandomSequence, 'backgroundColor':self.backgroundColor, 'sequenceLength':sequenceLength}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorSequenceRepeating(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE):
		"""
		colorSequence:List[Pixel]
			list of colors to in the pattern being shifted across the LED string
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self.backgroundColor = backgroundColor
			self.colorSequence = LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence)
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorSequenceRepeating, 'backgroundColor':self.backgroundColor, 'colorSequence':self.colorSequence}
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorTransition(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE, stepsPerTransition:int=5, wrap:bool=True):
		"""
		stepsPerTransition: int
			how many pixels it takes to transition from one color to the next
		wrap: bool
			if true, the last color of the sequence will transition to the first color as the final transition
		backgroundColor:Pixel
			color to set any LED that isn't part of the pattern
		colorSequence:List[Pixel]
			list of colors to cycles through setting all LEDs at once
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor
			self.colorSequence = LightPattern.ColorTransitionArray(arrayLength=len(colorSequence)*int(stepsPerTransition),wrap=True, colorSequence=colorSequence)
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorTransition, 'backgroundColor':self.backgroundColor, 'colorSequence':self.colorSequence, 'stepsPerTransition':stepsPerTransition, 'wrap':wrap}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorTransitionRepeating(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, colorSequence:List[Pixel]=DEFAULT_COLOR_SEQUENCE, stepsPerTransition:int=5, wrap:bool=True):
		"""
		colorSequence:List[Pixel]
			list of colors to in the pattern being shifted across the LED string
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			colorSequence = LightPattern.ColorTransitionArray(arrayLength=(len(colorSequence)*stepsPerTransition), wrap=wrap, colorSequence=colorSequence)
			arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self.backgroundColor = backgroundColor
			self.colorSequence = LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence)
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorTransitionRepeating, 'backgroundColor':self.backgroundColor, 'colorSequence':self.colorSequence, 'stepsPerTransition':stepsPerTransition, 'wrap':wrap}
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorRainbow(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, rainbowPixels:int=50):
		"""
		Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

		rainbowPixels:int
			when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor
			self.colorSequence = LightPattern.RainbowArray(arrayLength=rainbowPixels)
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorTransitionRepeating, 'backgroundColor':self.backgroundColor, 'rainbowPixels':rainbowPixels}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def useColorRainbowRepeating(self, backgroundColor:Pixel=DEFAULT_BACKGROUND_COLOR, rainbowPixels:int=10):
		"""
		Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

		rainbowPixels:int
			when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.backgroundColor = backgroundColor
			self.colorSequence = LightPattern.RainbowArray(arrayLength=rainbowPixels)
			arrayLength = np.ceil(self._LEDCount / len(self.colorSequence)) * len(self.colorSequence)
			self.colorSequence = LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=self.colorSequence)
			if self.colorSequenceCount < self._LEDCount:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self._LEDCount))
			else:
				self._SetVirtualLEDArray(LightPattern.PixelArray(self.colorSequenceCount))
			self._colorFunction = {'function':self.useColorRainbowRepeating, 'backgroundColor':self.backgroundColor, 'rainbowPixels':rainbowPixels}
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise



	def functionSolidColor(self, refreshDelay:float=0.1):
		"""
		Set all LEDs to the same color

		refreshDelay: float
			delay between color updates
		backgroundColor: Pixel
			the pixel color to use for the base LED color
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._SolidColor_Function, configurationPointer=self._SolidColor_Configuration)
			# self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			# self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _SolidColor_Configuration(self):
		"""

		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._VirtualLEDArray = LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.colorSequence[0])
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _SolidColor_Function(self):
		try:
			pass
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionSolidColorCycle(self, refreshDelay:float=0.1):
		"""
		Set all LEDs to a single color at once, but cycles between a list of colors

		refreshDelay: float
			delay between color updates
		colorSequence:List[Pixel]
			list of colors to cycles through setting all LEDs at once
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._SolidColorCycle_Function, configurationPointer=self._SolidColorCycle_Configuration)
			# self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=None)
			# self._Cycle_Configuration(colorSequence=colorSequence)
			# self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			# self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _SolidColorCycle_Configuration(self):
		"""
		Cycles the entire LED string between colors in the sequence
		setting the entire array to to one color at a time

		Paramters:
			RGBTupleArray: array(tuple(int,int,int))
				sequence of colors to cycles the lights between
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			# self.colorSequence = colorSequence
			# self._FunctionList.append(self._Cycle_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _SolidColorCycle_Function(self):
		try:
			self._VirtualLEDArray *= 0
			self._VirtualLEDArray += self.colorSequenceNext
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionShift(self, refreshDelay:float=0.1, shiftAmount:int=1):
		"""
		Shifts a color pattern across the LED string marquee style.
		Uses the provided sequence of colors.

		refreshDelay: float
			delay between color updates
		backgroundColor: Pixel
			the pixel color to use for the base LED color
		colorSequence:List[Pixel]
			list of colors in the sequence being shifted
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Shift_Function, configurationPointer=self._Shift_Configuration, shiftAmount=shiftAmount)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Shift_Configuration(self, shiftAmount:int):
		"""
		Shifts each element in the array by 'shiftAmount' places

		Parameters:
			shiftAmount: int
				the amount by which to shift each element
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._ShiftAmount = shiftAmount
			self._VirtualLEDArray[:self.colorSequenceCount] = self.colorSequence
			# self._FunctionList.append(self._Shift_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Shift_Function(self):
		"""
		"""
		try:
			self._VirtualLEDIndexArray[:self._VirtualLEDIndexCount] = np.roll(self._VirtualLEDIndexArray[:self._VirtualLEDIndexCount], self._ShiftAmount, 0)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionShiftFade(self, refreshDelay:float=0.05, shiftAmount:int=1, fadeStepCount:int=10):
		"""
		Shift a color pattern across the LED string marquee style fading from color to color.

		refreshDelay: float
			delay between color updates
		shiftAmount: int
			each time the pattern shifts, shift it by this many LEDs
		fadeStepCount: int
			the number of fade steps between one color and the next
		backgroundColor:Pixel
			color to set any LED that isnt part of the shifting pattern
		colorSequence:List[Pixel]
			list of colors to in the pattern being shifted across the LED string
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._ShiftFade_Function, configurationPointer=self._ShiftFade_Configuration, shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _ShiftFade_Configuration(self, shiftAmount:int, fadeStepCount:int):
		"""
		Shifts each element in the array by 'shift' places

		Parameters:
			shift: int
				the amount by which to shift each element
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._ShiftAmount = shiftAmount
			self._FadeStepCounter = self._VirtualLEDCount
			self._FadeStepCount = fadeStepCount
			self._DefaultColorIndices = []
			self._FadeInColorIndices = []
			# self._FunctionList.append(self._ShiftFade_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _ShiftFade_Function(self):
		try:
			if self._FadeStepCounter >= self._FadeStepCount:
				for LEDindex in range(self._VirtualLEDCount):
					self._VirtualLEDArray[LEDindex,:] = self._VirtualLEDBuffer[LEDindex, :]
				self._VirtualLEDBuffer = np.roll(self._VirtualLEDBuffer, self._ShiftAmount, 0)
				self._FadeStepCounter = 0
			else:
				self._FadeStepCounter += 1
				for LEDindex in range(self._VirtualLEDCount):
					# self._FadeLED(LEDindex, self._VirtualLEDBuffer[LEDindex], self._FadeAmount)
					for RGBindex in range(3):
						step = int(((self._VirtualLEDBuffer[((LEDindex + self._ShiftAmount) % self._VirtualLEDCount), RGBindex] - self._VirtualLEDBuffer[LEDindex, RGBindex]) // self._FadeStepCount))
						self._VirtualLEDArray[LEDindex,RGBindex] -= step
						if self._VirtualLEDArray[LEDindex,RGBindex] > 255:
							self._VirtualLEDArray[LEDindex,RGBindex] = 255
						elif self._VirtualLEDArray[LEDindex,RGBindex] < 0:
							self._VirtualLEDArray[LEDindex,RGBindex] = 0
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionAlternate(self, refreshDelay:float=0.03, shiftAmount:int=1):
		"""
		Shift a color pattern across the LED string marquee style and then bounce back.

		refreshDelay: float
			delay between color updates
		shiftAmount: int
			each time the pattern shifts, shift it by this many LEDs
		backgroundColor:Pixel
			color to set any LED that isnt part of the shifting pattern
		colorSequence:List[Pixel]
			list of colors to in the pattern being shifted across the LED string
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			# arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Alternate_Function, configurationPointer=self._Alternate_Configuration, shiftAmount=shiftAmount)
			# self._Alternate_Configuration(refreshDelay=refreshDelay)
			# self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=colorSequence)
			# self._Alternate_Configuration(shiftAmount=shiftAmount)
			# self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			# self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Alternate_Configuration(self, shiftAmount:int):
		"""
		Shift the array several times in one direction, then back

		Parameters:
			shiftAmount: int
				the amount by which to shift the array each time

			shiftCount: int
				the number of times to shift the array before
				reversing direction

			flipLength: int

		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._LightDataObjects = []
			for i in range(self.colorSequenceCount):
				alternator = LightData(self.colorSequenceNext)
				alternator.index = i
				# alternator.stepCounter = i
				alternator.step = 1
				alternator.shiftAmount = shiftAmount
				# alternator.stepCountMax = (self._VirtualLEDCount - 1)
				# alternator.flipLength = self.colorSequenceCount
				alternator.direction = 1
				self._LightDataObjects.append(alternator)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Alternate_Function(self):
		try:
			self._off()
			for alternator in self._LightDataObjects:
				self._VirtualLEDArray[alternator.index] = alternator.colors[alternator.colorIndex]
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionCylon(self, refreshDelay:float=0.01, fadeAmount:int=15):
		"""
		Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

		refreshDelay: float
			delay between color updates
		fadeAmount: int
			how much each pixel fades per refresh
			smaller numbers = larger tails on the cylon eye fade
		foregroundColor:Pixel
			the color of the cylon eye pupil
		backgroundColor:Pixel
			color to set any LED that isnt part of the shifting pattern
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Cylon_Function, configurationPointer=self._Cylon_Configuration, fadeAmount=fadeAmount)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cylon_Configuration(self, fadeAmount:int):
		try:
			LOGGER.log(5,'%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._LightDataObjects = []
			for index, color in enumerate(self.colorSequence):
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cylon_Function(self):
		try:
			self._Fade(fadeAmount=self._LightDataObjects[0].fadeAmount)
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
					self._VirtualLEDArray[i] = eye.colors[eye.colorIndex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionMerge(self, refreshDelay:float=0.1, mergeSegmentLength:int=None):
		"""
		Reflect a color sequence and shift the reflections toward each other in the middle

		refreshDelay: float
			delay between color updates
		colorSequence:List[Pixel]
			the list of colors
		backgroundColor:Pixel
			color to set any LED that isnt part of the shifting pattern
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			# arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self._initializeFunction(refreshDelay=refreshDelay, functionPointer=self._Merge_Function, configurationPointer=self._Merge_Configuration, mergeSegmentLength=mergeSegmentLength)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
			self._SetVirtualLEDArray(LightPattern.ReflectArray(arrayLength=arrayLength, colorSequence=self.colorSequence, foldLength=self.colorSequenceCount))

		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Merge_Function(self):
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def functionAccelerate(self, beginDelay:float=0.1, endDelay:float=0.0001, delaySteps:int=None):
		"""
		Shifts a color pattern across the LED string marquee style, but accelerates as it goes.
		Uses the provided sequence of colors.

		beginDelay: float
			initial delay between color updates
		endDelay: float
			final delay between color updates
		delaySteps: int
			the number of times the marquee will accelerate from beginDelay to endDelay
		backgroundColor: Pixel
			the pixel color to use for the base LED color
		colorSequence:List[Pixel]
			list of colors to cycles through setting all LEDs at once
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._initializeFunction(refreshDelay=beginDelay, functionPointer=self._Accelerate_Function, configurationPointer=self._Accelerate_Configuration, shiftAmount=1, beginDelay=beginDelay, endDelay=endDelay, delaySteps=delaySteps)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Accelerate_Configuration(self, shiftAmount:int, beginDelay:float, endDelay:float, delaySteps:int):
		"""
		incrementally decreases the amount of self.refreshDelay between each shift
		for 'delaySteps' then maintains 'endDelay'

		Parameters:
			shift: int
				the amount to shift each time

			beginDelay: float
				the number of seconds to delay at the beginning

			endDelay: float
				the number of seconds to delay at the end

			delaySteps: int
				the number of times to increment
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if delaySteps is None:
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
			for i in range(self.colorSequenceCount):
				self._VirtualLEDArray[i] = self.colorSequenceNext
			# self._FunctionList.append(self._Accelerate_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Accelerate_Function(self):
		try:
			self._Shift_Function()
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_RandomChange_ColorList(self, refreshDelay:float=0.05, changeChance:float=0.01, colorSequence:List[Pixel]=[PixelColors.RED, PixelColors.GREEN, PixelColors.WHITE], twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Randomly changes pixels on the string to one of the provided colors

		refreshDelay: float
			delay between color updates
		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)
		colorSequence:List[Pixel]
			list of colors to cycles through setting all LEDs at once
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.PseudoRandomArray(arrayLength=self._LEDCount, colorSequence=colorSequence))
			self._RandomChange_Configuration(changeChance=changeChance, colorSequence=colorSequence)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChange_PseudoRandomColors(self, refreshDelay:float=0.05, changeChance:float=0.01, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Randomly changes pixels on the string to a random named color

		refreshDelay: float
			delay between color updates
		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.PseudoRandomArray(arrayLength=self._LEDCount))
			self._RandomChange_Configuration(changeChance=changeChance, colorSequence=PixelColors.pseudoRandom)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChange_RandomcolorSequence(self, refreshDelay:float=0.05, changeChance:float=0.01, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Randomly changes pixels on the string to a randomly generated RGB value

		refreshDelay: float
			delay between color updates
		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RandomArray(arrayLength=self._LEDCount))
			self._RandomChange_Configuration(changeChance=changeChance, colorSequence=PixelColors.random)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChange_Configuration(self, changeChance:float, colorSequence:List[Pixel]):
		"""
		Makes random changes to the LED array

		Parameters:
			changeChance: float
				a floating point number specifying the chance of
				modifying any given LED's value
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._RandomChangeChance = changeChance
			self.colorSequence = colorSequence
			self._FunctionList.append(self._RandomChange_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChange_Function(self):
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_RandomChangeFade_ColorList(self, refreshDelay:float=0.001, changeChance:float=0.2, fadeStepCount:int=30, backgroundColor:Pixel=PixelColors.WHITE, colorSequence:List[Pixel]=[PixelColors.RED,PixelColors.RED,PixelColors.GREEN,PixelColors.GREEN], twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Randomly changes pixels on the string to one of the provided colors by fading from one color to the next

		refreshDelay: float
			delay between color updates
		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)
		fadeStepCount: int
			number of steps in the transition from one color to the next
		colorSequence:List[Pixel]
			list of colors to cycles through setting all LEDs at once
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.PseudoRandomArray(arrayLength=self._LEDCount, colorSequence=colorSequence))
			self._RandomChangeFade_Configuration(fadeInChance=changeChance, fadeStepCount=fadeStepCount, colorSequence=colorSequence)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChangeFade_PseudoRandomColors(self, refreshDelay=0.001, changeChance=0.1, fadeStepCount=30, backgroundColor=PixelColors.OFF, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Randomly changes pixels on the string to a named color by fading from one color to the next

		refreshDelay: float
			delay between color updates
		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)
		fadeStepCount: int
			number of steps in the transition from one color to the next
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.PseudoRandomArray(arrayLength=self._LEDCount))
			self._RandomChangeFade_Configuration(fadeInChance=changeChance, fadeStepCount=fadeStepCount, colorSequence=PixelColors.pseudoRandom)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChangeFade_RandomColors(self, refreshDelay:float=0.001, changeChance:float=0.1, fadeStepCount:int=30, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Randomly changes pixels on the string to a random color by fading from one color to the next

		refreshDelay: float
			delay between color updates
		changeChance: float
			chance that any one pixel will change colors each update (from 0.0, to 1.0)
		fadeStepCount: int
			number of steps in the transition from one color to the next
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RandomArray(arrayLength=self._LEDCount))
			self._RandomChangeFade_Configuration(fadeInChance=changeChance, fadeStepCount=fadeStepCount, colorSequence=PixelColors.random)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChangeFade_Configuration(self, fadeInChance:float, fadeStepCount:int, colorSequence:List[Pixel]):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeChance = fadeInChance
			self._FadeStepCount = fadeStepCount
			self._FadeAmount = 255 // self._FadeStepCount
			self._FadeStepCounter = 0
			self._PreviousIndices = []
			self.colorSequence = colorSequence
			self._FunctionList.append(self._RandomChangeFade_Function)
			indices = self._GetRandomIndices(self._FadeChance)
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChangeFade_Function(self):
		try:
			for randomFade in self._LightDataObjects:
				self._FadeLED(led_index=randomFade.index, offColor=randomFade.colors[randomFade.colorIndex], fadeAmount=randomFade.fadeAmount)
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
					self._PreviousIndices.append(index)
					randomfade = LightData(self.colorSequenceNext)
					randomfade.index = index
					randomfade.fadeAmount = self._FadeAmount
					randomfade.stepCountMax = self._FadeStepCount
					self._LightDataObjects.append(randomfade)
				for index in defaultIndices:
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
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Meteors_ColorList(self, refreshDelay:float=0.01, fadeStepCount:int=4, maxSpeed:int=2, backgroundColor:Pixel=PixelColors.OFF, colorSequence:List[Pixel]=[PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.RED], twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail

		refreshDelay: float
			delay between color updates
		fadeStepCount: int
			this is the length of the meteor trail
		maxSpeed: int
			the amount be which the meteor moves each refresh
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		colorSequence:List[Pixel]
			list of colors to cycles through setting all LEDs at once
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=int(self._LEDCount*1.2), color=backgroundColor))
			self._Meteors_Configuration(colorSequence=colorSequence, fadeStepCount=fadeStepCount, maxSpeed=maxSpeed, randomColorCount=None)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Meteors_PseudoRandomColorList(self, refreshDelay:float=0.01, fadeStepCount:int=8, maxSpeed:int=2, randomColorCount:int=None, backgroundColor:Pixel=PixelColors.OFF, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		creates several 'meteors' from random named colors that will fly around the light string leaving a comet trail

		refreshDelay: float
			delay between color updates
		fadeStepCount: int
			this is the length of the meteor trail
		maxSpeed: int
			the amount be which the meteor moves each refresh
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		randomColorCount: int
			the number of random color meteors
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,7)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=int(self._LEDCount*1.2), color=backgroundColor))
			self._Meteors_Configuration(colorSequence=PixelColors.pseudoRandom, fadeStepCount=fadeStepCount, maxSpeed=maxSpeed, randomColorCount=randomColorCount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Meteors_RandomColorList(self, refreshDelay:float=0.01, fadeStepCount:int=8, maxSpeed:int=2, randomColorCount:int=None, backgroundColor=PixelColors.OFF, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		creates several 'meteors' from random named colors that will fly around the light string leaving a comet trail

		refreshDelay: float
			delay between color updates
		fadeStepCount: int
			this is the length of the meteor trail
		maxSpeed: int
			the amount be which the meteor moves each refresh
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		randomColorCount: int
			the number of random color meteors
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(1,7)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=int(self._LEDCount*1.2), color=backgroundColor))
			self._Meteors_Configuration(colorSequence=PixelColors.random, fadeStepCount=fadeStepCount, maxSpeed=maxSpeed, randomColorCount=randomColorCount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Configuration(self, fadeStepCount:int, maxSpeed:int, colorSequence:List[Pixel], randomColorCount:int):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if not callable(colorSequence):
				self.colorSequence = colorSequence
			else:
				self.colorSequence = colorSequence
				self.colorSequenceCount = randomColorCount

			for index in range(self.colorSequenceCount):
				meteor = LightData(self.colorSequenceNext)
				meteor.index = random.randint(0,self._VirtualLEDIndexCount-1)
				meteor.step = (-maxSpeed,maxSpeed)[random.randint(0,1)]
				while meteor.step == 0:
					meteor.step = random.randint(-maxSpeed,maxSpeed)
				meteor.stepCountMax = random.randint(2, self._VirtualLEDIndexCount-1)
				meteor.colorSequenceIndex = index
				self._LightDataObjects.append(meteor)
			self._FadeAmount = int(255 / fadeStepCount)
			self._MaxSpeed = maxSpeed
			self._FunctionList.append(self._Meteors_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Function(self):
		try:
			for ledIndex in range(len(self._VirtualLEDArray)):
				for rgbIndex in range(len(self._VirtualLEDArray[ledIndex])):
					if self._VirtualLEDArray[ledIndex][rgbIndex] - self._FadeAmount >= self.backgroundColor.tuple[rgbIndex]:
						self._VirtualLEDArray[ledIndex][rgbIndex] -= self._FadeAmount
					elif self._VirtualLEDArray[ledIndex][rgbIndex] + self._FadeAmount <= self.backgroundColor.tuple[rgbIndex]:
						self._VirtualLEDArray[ledIndex][rgbIndex] += self._FadeAmount
					else:
						self._VirtualLEDArray[ledIndex][rgbIndex] = self.backgroundColor.tuple[rgbIndex]
			for meteor in self._LightDataObjects:
				newLocation = (meteor.index + meteor.step) % self._VirtualLEDIndexCount
				meteor.index = newLocation
				meteor.stepCounter += 1
				if meteor.stepCounter >= meteor.stepCountMax:
					meteor.stepCounter = 0
					meteor.step = (-self._MaxSpeed, self._MaxSpeed)[random.randint(0,1)]
					meteor.stepCountMax = random.randint(2,self._VirtualLEDIndexCount*2)
					meteor.colors = [self.colorSequenceNext]
					meteor.index = random.randint(0,self._VirtualLEDIndexCount-1)
				self._VirtualLEDArray[meteor.index] = meteor.colors[meteor.colorIndex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_MeteorsFancy_colorSequence(self, refreshDelay:float=0.03, fadeAmount:int=35, maxSpeed:int=2, cycleColors:bool=False, meteorCount:int=3, backgroundColor:Pixel=PixelColors.OFF, colorSequence:List[Pixel]=[PixelColors.WHITE, PixelColors.WHITE, PixelColors.RED, PixelColors.RED, PixelColors.GREEN], twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
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
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		colorSequence:List[Pixel]
			list of colors to cycles through setting all LEDs at once
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsFancy_Configuration(meteorCount=meteorCount, colorSequence=colorSequence, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors, randomColorCount=None)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsFancy_PseudoRandomcolorSequence(self, refreshDelay:float=0.03, fadeAmount:int=35, maxSpeed:int=2, cycleColors:bool=False, meteorCount=None, randomColorCount:int=None, backgroundColor:Pixel=PixelColors.OFF, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Creates several 'meteors' from a list of random named colors that will fly around the light string leaving a comet trail.
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
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		randomColorCount: int
			the number of colors in the random color sequence
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if meteorCount is None:
				meteorCount = random.randint(2,5)
			if randomColorCount is None:
				randomColorCount = random.randint(2,4)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsFancy_Configuration(meteorCount=meteorCount, colorSequence=PixelColors.pseudoRandom, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors, randomColorCount=randomColorCount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsFancy_RandomcolorSequence(self, refreshDelay:float=0.03, fadeAmount:int=35, maxSpeed:int=2, cycleColors:bool=False, meteorCount=None, randomColorCount:int=None, backgroundColor:Pixel=PixelColors.OFF, twinkleColors:Pixel=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Creates several 'meteors' from a randomly generated list of RGB values that will fly around the light string leaving a comet trail.
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
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		randomColorCount: int
			the number of colors in the random color sequence
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if meteorCount is None:
				meteorCount = random.randint(2,5)
			if randomColorCount is None:
				randomColorCount = random.randint(2,4)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsFancy_Configuration(meteorCount=meteorCount, colorSequence=PixelColors.random, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors, randomColorCount=randomColorCount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsFancy_Configuration(self, meteorCount:int, colorSequence:List[Pixel], maxSpeed:int, fadeAmount:int, cycleColors:bool, randomColorCount:int):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._MeteorCount = meteorCount
			if not callable(colorSequence):
				self.colorSequence = colorSequence
			else:
				self.colorSequence = colorSequence
				self.colorSequenceCount = randomColorCount
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
			self._FunctionList.append(self._MeteorsFancy_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsFancy_Function(self):
		try:
			self._Fade()
			for meteor in self._LightDataObjects:
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
					for i in range(0,len(meteor.colors)):
						self._VirtualLEDArray[(meteor.index + meteor.step * i) % self._VirtualLEDCount] = meteor.colors[(meteor.colorIndex + i) % len(meteor.colors)]
				if self._CycleColors:
					meteor.colorIndex = (meteor.colorIndex + 1) % len(meteor.colors)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_MeteorsBouncy_ColorList(self, refreshDelay:float=0.001, fadeAmount:int=25, maxSpeed:int=1, explode:bool=True, backgroundColor:Pixel=PixelColors.OFF, colorSequence:List[Pixel]=[PixelColors.WHITE, PixelColors.GREEN, PixelColors.RED]):
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
		meteorCount: int
			the number of meteors flying around
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		colorSequence: List[Pixel]
			the list of colors to make meteors from
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsBouncy_Configuration(colorSequence=colorSequence, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode, randomColorCount=None)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsBouncy_PseudoRandomColorList(self, refreshDelay:float=0.001, fadeAmount:int=25, maxSpeed:int=1, explode:bool=True, randomColorCount:int=None, backgroundColor:Pixel=PixelColors.OFF):
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
		meteorCount: int
			the number of meteors flying around
		backgroundColor: Pixel
			the color that pixels are when no meteor is present
		colorSequence: List[Pixel]
			the list of colors to make meteors from
		twinkleColors:List[Pixel]
			list of colors to twinkle
		twinkleChance:float
			chance (from 0.0 to 1.0) that a single LED will twinkle
		returns: None
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,4)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsBouncy_Configuration(colorSequence=PixelColors.pseudoRandom, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode, randomColorCount=randomColorCount)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsBouncy_RandomColorList(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=25, maxSpeed=1, explode=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,4)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsBouncy_Configuration(colorSequence=PixelColors.random, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode, randomColorCount=randomColorCount)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsBouncy_Configuration(self, colorSequence:List[Pixel], fadeAmount:int, maxSpeed:int, explode:bool, randomColorCount:int):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if not callable(colorSequence):
				self.colorSequence = colorSequence
			else:
				self.colorSequence = colorSequence
				self.colorSequenceCount = randomColorCount
			self._FadeAmount = fadeAmount
			self._MaxSpeed = maxSpeed
			self._Explode = explode
			otherSpeeds = []
			for index in range(self.colorSequenceCount):
				meteor = LightData(self.colorSequenceNext)
				meteor.index = random.randint(0, self._VirtualLEDCount -1)
				meteor.previousIndex = meteor.index
				meteor.step = (-maxSpeed, maxSpeed)[random.randint(0,1)]
				meteor.random = randomColorCount
				while abs(meteor.step) in otherSpeeds:
					if meteor.step > 0:
						meteor.step += 1
					else:
						meteor.step -= 1
				otherSpeeds.append(abs(meteor.step))
				meteor.colorSequenceIndex = index
				self._LightDataObjects.append(meteor)
			# make sure there are at least two going to collide
			if self._LightDataObjects[0].step * self._LightDataObjects[1].step > 0:
				self._LightDataObjects[1].step *= -1
			self._FunctionList.append(self._MeteorsBouncy_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsBouncy_Function(self):
		try:
			self._Fade()
			# move the meteors
			for meteor in self._LightDataObjects:
				# calculate next index
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
						if meteor.random:
							if random.randint(0,1000) > 800:
								meteor.colors = [self.colorSequenceNext]
						meteor.bounce = False
						if self._Explode:
							middle = meteor.moveRange[len(meteor.moveRange)//2]
							explosions.append(((middle-6) % self._VirtualLEDCount, Pixel(PixelColors.GRAY).array))
							explosions.append(((middle-5) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).array))
							explosions.append(((middle-4) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
							explosions.append(((middle-3) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
							explosions.append(((middle-2) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
							explosions.append(((middle-1) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
							explosions.append(((middle+1) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
							explosions.append(((middle+2) % self._VirtualLEDCount, Pixel(PixelColors.RED).array))
							explosions.append(((middle+3) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
							explosions.append(((middle+4) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).array))
							explosions.append(((middle+5) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).array))
							explosions.append(((middle+6) % self._VirtualLEDCount, Pixel(PixelColors.GRAY).array))
			for index, meteor in enumerate(self._LightDataObjects):
				try:
					if meteor.index > self._VirtualLEDCount-1:
						meteor.index = meteor.index % (self._VirtualLEDCount)
					for i in meteor.moveRange:
						self._VirtualLEDArray[i] = meteor.colors[meteor.colorIndex]
				except:
					# LOGGER.error('len(self._LightDataObjects)={},len(meteor[{}]={}, itms[{},{}] len(LEDS)={}'.format(len(self._LightDataObjects), led, len(self._LightDataObjects[led]), index, color, len(self._VirtualLEDArray)))
					raise
			if self._Explode and len(explosions) > 0:
				for x in explosions:
					self._VirtualLEDArray[x[0]] = x[1]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_MeteorsAgain_ColorList(self, refreshDelay=0.001, colorSequence=[PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN], backgroundColor=PixelColors.OFF, maxDelay=5, fadeSteps=25, randomColors=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			fadeAmount = 255//fadeSteps
			while (fadeAmount * fadeSteps) < 256:
				fadeAmount += 1
			self._MeteorsAgain_Configuration(colorSequence=colorSequence, maxDelay=maxDelay, fadeAmount=fadeAmount, fadeSteps=fadeSteps)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsAgain_PseudoRandomColorList(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=5, fadeSteps=25, randomColors=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			fadeAmount = 255//fadeSteps
			while (fadeAmount * fadeSteps) < 256:
				fadeAmount += 1
			if randomColorCount is None:
				randomColorCount = random.randint(3,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.pseudoRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			self._MeteorsAgain_Configuration(colorSequence=colorSequence, maxDelay=maxDelay, fadeAmount=fadeAmount, fadeSteps=fadeSteps)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsAgain_RandomColorList(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=5, fadeSteps=25, randomColors=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			fadeAmount = 255//fadeSteps
			while (fadeAmount * fadeSteps) < 256:
				fadeAmount += 1
			if randomColorCount is None:
				randomColorCount = random.randint(3,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			self._MeteorsAgain_Configuration(colorSequence=colorSequence, maxDelay=maxDelay, fadeAmount=fadeAmount, fadeSteps=fadeSteps)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsAgain_Configuration(self, colorSequence, maxDelay, fadeAmount, fadeSteps):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.colorSequence = colorSequence
			self._MaxDelay = maxDelay
			self._FadeAmount = fadeAmount
			self._FadeSteps = fadeSteps
			for index, color in enumerate(self.colorSequence):
				meteor = LightData(color)
				meteor.index = random.randint(0, self._VirtualLEDCount-1)
				meteor.direction = (-1,1)[random.randint(0, 1)]
				meteor.step = (-1,1)[random.randint(0, 1)]
				meteor.delayCountMax = random.randint(0, maxDelay)
				meteor.stepCountMax = random.randint(2, self._VirtualLEDCount*6)
				meteor.colorSequenceIndex = index
				self._LightDataObjects.append(meteor)
			self._FunctionList.append(self._MeteorsAgain_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsAgain_Function(self):
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
						# if self._RandomColors:
							# meteor.colors = COLORS_NO_OFF[COLORS_NO_OFF.keys()[random.randint(0,len(COLORS_NO_OFF.keys())-1)]]
			for ledIndex in range(len(self._VirtualLEDArray)):
				self._FadeLED(ledIndex, self.backgroundColor, self._FadeAmount/2)
			for meteor in self._LightDataObjects:
				self._VirtualLEDArray[meteor.index] = meteor.colors[meteor.colorIndex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Paint_ColorList(self, refreshDelay=0.001, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE,PixelColors.OFF], backgroundColor=PixelColors.OFF, maxDelay=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor))
			self._Paint_Configuration(randomColors=False, colorSequence=colorSequence, colorCount=len(colorSequence), maxDelay=maxDelay)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Paint_PseudoRandomColorList(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=10, randomColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor))
			self._Paint_Configuration(randomColors=True, colorSequence=PixelColors.pseudoRandom, colorCount=randomColorCount, maxDelay=maxDelay)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Paint_RandomColorList(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=10, randomColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor))
			self._Paint_Configuration(randomColors=True, colorSequence=PixelColors.random, colorCount=randomColorCount, maxDelay=maxDelay)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Paint_Configuration(self, randomColors, colorSequence, colorCount, maxDelay):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._RandomColors = randomColors
			self.colorSequence = colorSequence
			self._MaxDelay = maxDelay
			for i in range(colorCount):
				paintBrush = LightData(self.colorSequenceNext)
				paintBrush.index = random.randint(0, self._VirtualLEDCount-1)
				paintBrush.step = (-1, 1)[random.randint(0,1)]
				paintBrush.delayCountMax = random.randint(10, self._MaxDelay)
				paintBrush.stepCountMax = random.randint(2, self._VirtualLEDCount*2)
				paintBrush.colorSequenceIndex = i
				paintBrush.random = randomColors
				self._LightDataObjects.append(paintBrush)
			self._FunctionList.append(self._Paint_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Paint_Function(self):
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
							paintBrush.colors = [self.colorSequenceNext]
				self._VirtualLEDArray[paintBrush.index] = paintBrush.colors[paintBrush.colorIndex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Sprites_ColorList(self, refreshDelay=0.03, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE], backgroundColor=PixelColors.OFF, fadeAmount=15):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor))
			self._Sprites_Configuration(fadeAmount=fadeAmount, colorSequence=colorSequence, colorCount=len(colorSequence), randomColors=False)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Sprites_PseudoRandomColorList(self, refreshDelay=0.03, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor))
			self._Sprites_Configuration(fadeAmount=fadeAmount, colorSequence=PixelColors.pseudoRandom, colorCount=randomColorCount, randomColors=True)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Sprites_RandomColorList(self, refreshDelay=0.03, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor))
			self._Sprites_Configuration(fadeAmount=fadeAmount, colorSequence=PixelColors.random, colorCount=randomColorCount, randomColors=True)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Sprites_Configuration(self, fadeAmount, colorSequence, colorCount, randomColors):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeAmount = fadeAmount
			self.colorSequence = colorSequence
			for i in range(colorCount):
				sprite = LightData(self.colorSequenceNext)
				sprite.active = False
				sprite.index = random.randint(0, self._VirtualLEDCount-1)
				sprite.lastindex = sprite.index
				sprite.direction = [-1,1][random.randint(0,1)]
				sprite.colorSequenceIndex = i
				sprite.random = randomColors
				self._LightDataObjects.append(sprite)
			self._LightDataObjects[0].active = True
			self._FunctionList.append(self._Sprites_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Sprites_Function(self):
		try:
			self._Fade()
			for sprite in self._LightDataObjects:
				if sprite.active:
					still_alive = random.randint(6,40) > sprite.duration
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
								self._VirtualLEDArray[sprite.index] = sprite.colors[sprite.colorIndex]
								if not first:
									self._FadeLED(index, self.backgroundColor, self._FadeAmount)
								first - False
							#sprite[sprite_index] = ma
						else:
							for index in range(ma-1, mi-1,-1):
								index = index % self._VirtualLEDCount
								sprite.index = index
								self._VirtualLEDArray[sprite.index] = sprite.colors[sprite.colorIndex]
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
						if sprite.random:
							sprite.colors = [self.colorSequenceNext]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Twinkle(self, refreshDelay=0.05, backgroundColor=PixelColors.OFF, twinkleChance=0.05, twinkleColors=[(80,80,80)]):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Peppermint(self):
		"""
		For Kaleigh
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.Do_Twinkle(refreshDelay=0.2, backgroundColor=(170,170,170), twinkleChance=0.3, twinkleColors=[PixelColors.PURPLE])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Girly(self):
		"""
		For Emily and Lily
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.Do_Twinkle(refreshDelay=0.2, backgroundColor=(170,170,170), twinkleChance=0.3, twinkleColors=[PixelColors.PINK, PixelColors.VIOLET, PixelColors.RED])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Twinkle_Configuration(self, twinkleChance, twinkleColors):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._TwinkleChance = float(twinkleChance)
			self._TwinkleColorList = LightPattern.ConvertPixelArrayToNumpyArray(twinkleColors)
			self._OverlayList.append(self._Twinkle_Overlay)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Twinkle_Overlay(self):
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
			maxVal = 1000
			if self._TwinkleChance > 0.0:
				for color in self._TwinkleColorList:
					for LEDIndex in range(self._LEDCount):
						doLight = random.randint(0,maxVal)
						if doLight > maxVal * (1.0 - self._TwinkleChance):
							self._LEDArray[LEDIndex] = color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Spaz(self, refreshDelay=0.02, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE], twinkleColors=[PixelColors.CYAN], blinkColors=[PixelColors.OFF, PixelColors.WHITE], shiftAmount=7, twinkleChance=0.5, blinkChance=0.5):
		"""
		For annoying people
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.ColorTransitionArray(arrayLength=self._LEDCount, colorSequence=colorSequence))
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Blink_Configuration(blinkChance=blinkChance, blinkColors=blinkColors)
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Blink_Configuration(self, blinkChance, blinkColors):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._BlinkChance = float(blinkChance)
			self._BlinkColorList = LightPattern.ConvertPixelArrayToNumpyArray(blinkColors)
			self._OverlayList.append(self._Blink_Overlay)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
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
				for color in self._BlinkColorList:
					maxVal = 1000
					doBlink = random.randint(0, maxVal)
					if doBlink > maxVal * (1.0 - self._BlinkChance):
						for LEDIndex in range(self._LEDCount):
							self._LEDArray[LEDIndex] = color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Raindrops_ColorList(self, refreshDelay=0.05, colorSequence=[PixelColors.RED, PixelColors.GREEN, PixelColors.WHITE], maxSize=15, backgroundColor=PixelColors.OFF, fadeAmount=25):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			self._Raindrops_Configuration(colorSequence=colorSequence, colorCount=len(colorSequence), fadeAmount=fadeAmount, maxSize=maxSize, randomColors=False)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Raindrops_PseudoRandomColorList(self, refreshDelay=0.05, randomColorCount=None, maxSize=15, backgroundColor=PixelColors.OFF, fadeAmount=25):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			self._Raindrops_Configuration(colorSequence=PixelColors.pseudoRandom, colorCount=randomColorCount, fadeAmount=fadeAmount, maxSize=maxSize, randomColors=True)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Raindrops_RandomColorList(self, refreshDelay=0.05, randomColorCount=None, maxSize=15, backgroundColor=PixelColors.OFF, fadeAmount=25):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			self._Raindrops_Configuration(colorSequence=PixelColors.random, colorCount=randomColorCount, fadeAmount=fadeAmount, maxSize=maxSize, randomColors=True)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Raindrops_Configuration(self, colorSequence, colorCount, fadeAmount, maxSize, randomColors):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeAmount = fadeAmount
			self.colorSequence = colorSequence
			for i in range(colorCount):
				raindrop = LightData(self.colorSequenceNext)
				raindrop.maxSize = maxSize
				raindrop.index = random.randint(0, self._VirtualLEDCount-1)
				raindrop.stepCountMax = random.randint(2, raindrop.maxSize//2)
				raindrop.fadeAmount = 192 // raindrop.stepCountMax
				raindrop.active = False
				raindrop.activeChance = 0.2
				raindrop.colorSequenceIndex = i
				raindrop.random = randomColors
				self._LightDataObjects.append(raindrop)
			self._LightDataObjects[0].active = True
			self._FunctionList.append(self._Raindrops_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Raindrops_Function(self):
		try:
			self._Fade()
			for raindrop in self._LightDataObjects:
				if not raindrop.active:
					chance = random.randint(0, 1000) / 1000
					if chance < raindrop.activeChance:
						raindrop.active = True
				if raindrop.active:
					if raindrop.stepCounter < raindrop.stepCountMax:
						self._VirtualLEDArray[(raindrop.index + raindrop.stepCounter) % self._VirtualLEDCount] = raindrop.colors[raindrop.colorIndex]
						self._VirtualLEDArray[(raindrop.index - raindrop.stepCounter)] = raindrop.colors[raindrop.colorIndex]
						raindrop.colors[raindrop.colorIndex] = self._FadeColor(raindrop.colors[raindrop.colorIndex], fadeAmount=raindrop.fadeAmount)
						raindrop.stepCounter += 1
					else:
						raindrop.index = random.randint(0, self._VirtualLEDCount-1)
						raindrop.stepCountMax = random.randint(2, raindrop.maxSize//2)
						raindrop.fadeAmount = 192 // raindrop.stepCountMax
						raindrop.stepCounter = 0
						raindrop.colors = [self.colorSequenceNext]
						raindrop.active = False
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def demo(self, secondsPerMode=20):
		try:
			self.secondsPerMode = secondsPerMode
			omitted = [LightFunction.Do_Spaz.__name__, LightFunction.Do_SolidColor_SinglePseudoRandomColor.__name__, LightFunction.Do_SolidColor_SinglePseudoRandomColor.__name__, LightFunction.Do_SolidColor_SingleRandomColor.__name__]
			funcs = list(dir(self))
			funcs = [f  for f in funcs if f.lower()[:3] == 'do_' and not f in omitted]
			while True:
				try:
					getattr(self, funcs[random.randint(0, len(funcs)-1)])()
				except Exception as ex:
					LOGGER.error(ex)
		except SystemExit:
			pass
		except KeyboardInterrupt:
			pass
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def test(self, secondsPerMode=0.5, function_names=[], color_names=[]):
		try:
			self.secondsPerMode = secondsPerMode
			attrs = list(dir(self))
			funcs = [f for f in attrs if f[:8] == 'function']
			colors = [c for c in attrs if c[:8] == 'useColor']
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
			for f in funcs:
				for c in colors:
					getattr(self, f)()
					getattr(self, c)()
					self.run()
		except SystemExit:
			pass
		except KeyboardInterrupt:
			pass
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

