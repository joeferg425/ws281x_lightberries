import numpy as np
import time
import random
import logging
import inspect
from typing import List, Tuple, Optional
from .LightPatterns import LightPattern, LightString, Pixel, PixelColors

LOGGER = logging.getLogger()
logging.addLevelName(5, 'VERBOSE')
if not LOGGER.handlers:
	streamHandler = logging.StreamHandler()
	LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)

DEFAULT_TWINKLE_CHANCE = 0.0
DEFAULT_TWINKLE_COLOR = PixelColors.GRAY

class LightFunction:
	def __init__(self, lights:LightString, debug:bool=False, verbose:bool=False):
		try:
			if True == debug or True == verbose:
				LOGGER.setLevel(logging.DEBUG)
			if True == verbose:
				LOGGER.setLevel(5)
			self._LEDArray = lights
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

			self.__RefreshDelay = 0.001
			self.__SecondsPerMode = 120
			self.__BackgroundColor = PixelColors.OFF
			self.__ColorSequence = LightPattern.ConvertPixelArrayToNumpyArray([])
			self.__ColorSequenceCount = 0
			self.__ColorSequenceIndex = 0

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
			self._ShiftDirection = 1
			self._flipLength = 0
			self._RandomChangeChance = 0.0
			self._AccelerateIndex = 0
			self._MeteorCount = 0
			self._LightDataObjects = []
			self._MaxSpeed = 0
			self._CycleColors = False
			self._FadeAmount = 0
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
	def RefreshDelay(self)->float:
		return self.__RefreshDelay
	@RefreshDelay.setter
	def RefreshDelay(self, delay):
		self.__RefreshDelay = float(delay)

	@property
	def BackgroundColor(self)->Pixel:
		return self.__BackgroundColor
	@BackgroundColor.setter
	def BackgroundColor(self, color:Pixel):
		self.__BackgroundColor = Pixel(color)

	@property
	def SecondsPerMode(self)->float:
		return self.__SecondsPerMode
	@SecondsPerMode.setter
	def SecondsPerMode(self, seconds:float):
		self.__SecondsPerMode = float(seconds)

	@property
	def ColorSequence(self)->np.ndarray:
		return self.__ColorSequence
	@ColorSequence.setter
	def ColorSequence(self, colorSequence:List[Pixel]):
		if not callable(colorSequence):
			self.__ColorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			self.ColorSequenceCount = len(self.__ColorSequence)
			self.ColorSequenceIndex = 0
		else:
			self.__ColorSequence = colorSequence
			self.ColorSequenceCount = None
			self.ColorSequenceIndex = None

	@property
	def ColorSequenceCount(self)->int:
		return self.__ColorSequenceCount
	@ColorSequenceCount.setter
	def ColorSequenceCount(self, colorSequenceCount:int):
		self.__ColorSequenceCount = colorSequenceCount

	@property
	def ColorSequenceIndex(self)->int:
		return self.__ColorSequenceIndex
	@ColorSequenceIndex.setter
	def ColorSequenceIndex(self, colorSequenceIndex:int):
		self.__ColorSequenceIndex = colorSequenceIndex

	@property
	def ColorSequenceNext(self):
		if not callable(self.ColorSequence):
			temp = self.ColorSequence[self.ColorSequenceIndex]
			self.ColorSequenceIndex += 1
			if self.ColorSequenceIndex >= self.ColorSequenceCount:
				self.ColorSequenceIndex = 0
		else:
			temp = self.ColorSequence().array
		return temp

	def _Initialize(self, refreshDelay, backgroundColor, ledArray):
		try:
			self.RefreshDelay = refreshDelay
			self.BackgroundColor = backgroundColor
			self._SetVirtualLEDArray(ledArray)
			self._ShiftDirection = 1
			self._ShiftCount = 0
			self._FunctionList = []
			self._OverlayList = []
			self._TwinkleChance = 0
			self._TwinkleColorList = []
			self._LightDataObjects = []
			self._AccelerateIndex = 0
			self._ColorSequenceIndex = 0
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
				self._VirtualLEDArray = LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.BackgroundColor)
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

	def _RunFunctions(self):
		try:
			for function in self._FunctionList:
				function()
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

	def _GetRandomIndices(self, getChance=0.1):
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

	def _Fade(self):
		"""
		"""
		try:
			[self._FadeLED(i, self.BackgroundColor, self._FadeAmount) for i in range(len(self._VirtualLEDArray))]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _FadeLED(self, led_index, offColor=None, fadeAmount=None):
		try:
			if offColor is None:
				offColor = self.BackgroundColor
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

	def _FadeColor(self, color, offColor=None, fadeAmount=None):
		try:
			if offColor is None:
				offColor = self.BackgroundColor
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

	def _Run(self):
		try:
			if self._NextModeChange is None:
				self._LastModeChange = time.time()
				if self.SecondsPerMode is None:
					self._NextModeChange = self._LastModeChange + (random.uniform(30,120) )
				else:
					self._NextModeChange = self._LastModeChange + (self.SecondsPerMode )
			while time.time() < self._NextModeChange or self._LoopForever:
				try:
					self._RunFunctions()
					self._CopyVirtualLedsToWS281X()
					self._RunOverlays()
					self._RefreshLEDs()
					time.sleep(self.RefreshDelay)
				except KeyboardInterrupt:
					raise
				except SystemExit:
					raise
				except Exception as ex:
					LOGGER.error('_Run Loop Error: {}'.format(ex))
					raise
			self._LastModeChange = time.time()
			if self.SecondsPerMode is None:
				self._NextModeChange = self._LastModeChange + (random.random(30,120) )
			else:
				self._NextModeChange = self._LastModeChange + (self.SecondsPerMode )
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_SolidColor(self, refreshDelay=0.5, backgroundColor=PixelColors.WHITE, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Set all LEDs to the same color

		backgroundColor: Pixel
			the pixel color
		"""
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

	def Do_SolidColor_RandomColor(self, refreshDelay=0.5, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			backgroundColor = PixelColors.random()
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

	def Do_SolidColor_TruRandomColor(self, refreshDelay=0.5, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			backgroundColor = PixelColors.trueRandom()
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


	def Do_SolidColor_Cycle_Sequence(self, refreshDelay=0.5, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE], twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=None)
			self._Cycle_Configuration(colorSequence=colorSequence)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_SolidColor_Cycle_Rainbow(self, refreshDelay=0.5, segmentLength=75, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=None)
			self._Cycle_Configuration(colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength))
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_SolidColor_Cycle_RandomColors(self, refreshDelay=0.5, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=None)
			self._Cycle_Configuration(colorSequence=PixelColors.random)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_SolidColor_Cycle_TrueRandomColors(self, refreshDelay=0.5, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=None)
			self._Cycle_Configuration(colorSequence=PixelColors.trueRandom)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cycle_Configuration(self, colorSequence:List[Pixel]):
		"""
		Cycles the entire LED string between colors in the sequence
		setting the entire array to to one color at a time

		Paramters:
			RGBTupleArray: array(tuple(int,int,int))
				sequence of colors to cycles the lights between
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.ColorSequence = colorSequence
			self._FunctionList.append(self._Cycle_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cycle_Function(self):
		try:
			self._VirtualLEDArray *= 0
			self._VirtualLEDArray += self.ColorSequenceNext
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Shift_Sequence(self, refreshDelay=0.1, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], backgroundColor=PixelColors.OFF, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE, shiftAmount=1):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Sequence_Repeating(self, refreshDelay=0.1, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], backgroundColor=PixelColors.OFF, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE, shiftAmount=1):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence))
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Sequence_RandomColors(self, refreshDelay=0.1, randomColorCount=None, backgroundColor=PixelColors.OFF, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE, shiftAmount=1):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(1,10)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Sequence_TrueRandomColors(self, refreshDelay=0.1, randomColorCount=None, backgroundColor=PixelColors.OFF, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE, shiftAmount=1):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(1,10)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.trueRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Rainbow(self, refreshDelay=0.1, shiftAmount=1, rainbowLength=None, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		RainbowChases! Unicorns!
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if rainbowLength is None:
				rainbowLength = self._LEDCount
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RainbowArray(arrayLength=rainbowLength))
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Emily1(self, refreshDelay=0.1, shiftAmount=1, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.Emily1())
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Lily1(self, refreshDelay=0.1, shiftAmount=1, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.ColorStretchArray())
			self._Shift_Configuration(shiftAmount=shiftAmount)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Shift_Configuration(self, shiftAmount:int=1):
		"""
		Shifts each element in the array by 'shiftAmount' places

		Parameters:
			shiftAmount: int
				the amount by which to shift each element
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._ShiftAmount = shiftAmount
			self._FunctionList.append(self._Shift_Function)
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


	def Do_Shift_Fade_Sequence(self, refreshDelay=0.05, colorSequence=[PixelColors.RED, PixelColors.WHITE, PixelColors.RED, PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], shiftAmount=1, fadeStepCount=10):
		"""
		Chase mode
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			sequenceLength = len(colorSequence)
			while len(colorSequence) < self._LEDCount:
				colorSequence = np.concatenate((colorSequence, colorSequence), 0)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Shift_Fade_Configuration(shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
			# self._Shift_Fade_Configuration(shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Fade_Sequence_RandomColors(self, refreshDelay=0.05, randomColorCount=None, shiftAmount=1, fadeStepCount=10):
		"""
		Chase mode
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Shift_Fade_Configuration(shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
			# self._Shift_Fade_Configuration(shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Fade_Sequence_TrueRandomColors(self, refreshDelay=0.05, randomColorCount=None, shiftAmount=1, fadeStepCount=10):
		"""
		Chase mode
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.trueRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Shift_Fade_Configuration(shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
			# self._Shift_Fade_Configuration(shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Shift_Fade_Configuration(self, shiftAmount=1, fadeStepCount=10):
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
			self._FunctionList.append(self._Shift_Fade_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Shift_Fade_Function(self):
		try:
			if self._FadeStepCounter >= self._FadeStepCount:
				for LEDindex in range(self._VirtualLEDCount):
					self._VirtualLEDArray[LEDindex,:] = self._VirtualLEDBuffer[LEDindex, :]
				self._VirtualLEDBuffer = np.roll(self._VirtualLEDBuffer, self._ShiftAmount, 0)
				self._FadeStepCounter = 0
			else:
				self._FadeStepCounter += 1
				for LEDindex in range(self._VirtualLEDCount):
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

	def _ModifyFade(self, color=PixelColors.WHITE, fadeIndices=None, step=25):
		try:
			if fadeIndices is None:
				fadeIndices = range(self._VirtualLEDCount)
			for LEDIndex in fadeIndices:
				self._FadeLED(led_index=LEDIndex, offColor=color, fadeAmount=step)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Alternate_Sequence(self, refreshDelay=0.05, shiftAmount=1, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Alternate_Configuration(shiftAmount=shiftAmount, arrayLength=arrayLength, segmentLength=len(colorSequence))
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Alternate_Sequence_RandomColors(self, refreshDelay=0.02, shiftAmount=1, randomColorCount=None, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(2, 10)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Alternate_Configuration(shiftAmount=shiftAmount, arrayLength=self._VirtualLEDCount-randomColorCount, segmentLength=None)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Alternate_Sequence_TrueRandomColors(self, refreshDelay=0.02, shiftAmount=1, randomColorCount=None, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(2, 10)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.trueRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Alternate_Configuration(shiftAmount=shiftAmount, arrayLength=self._VirtualLEDCount-randomColorCount, segmentLength=None)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Alternate_Sequence_Repeating(self, refreshDelay=0.05, shiftAmount=1, shiftCount=None, flipLength=None, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence)))
			self._Alternate_Configuration(shiftAmount=shiftAmount, arrayLength=len(colorSequence), segmentLength=0)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Alternate_Rainbow(self, refreshDelay=0.05, shiftAmount=1, segmentLength:int=None, arrayLength:int=None, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if segmentLength is None:
				segmentLength = 20
			if arrayLength is None:
				arrayLength = self._LEDCount
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RainbowArray(arrayLength=segmentLength))
			self._Alternate_Configuration(shiftAmount=shiftAmount, arrayLength=arrayLength, segmentLength=segmentLength)
			self._Twinkle_Configuration(twinkleChance=twinkleChance, twinkleColors=twinkleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Alternate_Configuration(self, shiftAmount:int, arrayLength:int, segmentLength:int):
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
			if arrayLength is None:
				arrayLength = (self._VirtualLEDCount - 1)
			self._ShiftAmount = shiftAmount
			self._ShiftCount = arrayLength
			self._ShiftCounter = 0
			self._flipLength = segmentLength
			self._FunctionList.append(self._Alternate_Function)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Alternate_Function(self):
		try:
			if self._ShiftCounter >= self._ShiftCount:
				self._ShiftCounter = 0
				self._ShiftDirection = self._ShiftDirection * -1
				if not self._flipLength is None:
					for segment in range(0, self._VirtualLEDCount, self._ShiftCount):
						temp = np.array(self._VirtualLEDArray[segment:segment+self._flipLength])
						for i in range(self._flipLength):
							self._VirtualLEDArray[segment+i] = temp[(self._flipLength-1)-i]
			else:
				self._VirtualLEDIndexArray = np.roll(self._VirtualLEDIndexArray, (self._ShiftDirection * self._ShiftAmount), 0)
				self._ShiftCounter += 1
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Cylon(self, refreshDelay=0.01, colorSequence=[PixelColors.RED], backgroundColor=PixelColors.OFF, fadeAmount=15, cylonSpeedup=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._Cylon_Configuration(refreshDelay, colorSequence, fadeAmount, cylonSpeedup)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Cylon_RandomColor(self, refreshDelay=0.01, backgroundColor=PixelColors.OFF, fadeAmount=15, cylonSpeedup=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			colorSequence = [PixelColors.random()]
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._Cylon_Configuration(refreshDelay, colorSequence, fadeAmount, cylonSpeedup)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Cylon_TrueRandomColor(self, refreshDelay=0.01, backgroundColor=PixelColors.OFF, fadeAmount=15, cylonSpeedup=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			colorSequence = [PixelColors.trueRandom()]
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._Cylon_Configuration(refreshDelay, colorSequence, fadeAmount, cylonSpeedup)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cylon_Configuration(self,refreshDelay, colorSequence, fadeAmount, cylonSpeedup):
		try:
			LOGGER.log(5,'%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.ColorSequence = colorSequence
			for index, color in enumerate(self.ColorSequence):
				eye = LightData(color)
				eye.step = 3
				eye.direction=1
				eye.colorSequenceIndex = index
				self._LightDataObjects.append(eye)
			self._FadeAmount = fadeAmount
			self._CylonSpeedup = cylonSpeedup
			self._FunctionList.append(self._Cylon_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Cylon_Function(self):
		try:
			self._Fade()
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
					self._VirtualLEDArray[i] = eye.colors[eye.colorindex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Merge_Sequence(self, refreshDelay=0.1, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.ReflectArray(arrayLength=arrayLength, colorSequence=colorSequence))
			self._Merge_Configuration(segmentLength=len(colorSequence))
			self._Twinkle_Configuration(twinkleColors=twinkleColors, twinkleChance=twinkleChance)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Merge_Sequence_RandomColors(self, refreshDelay=0.1, randomColorCount=None, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(2,6)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.ReflectArray(arrayLength=self._LEDCount, colorSequence=colorSequence))
			self._Merge_Configuration(segmentLength=(self._LEDCount // 2))
			self._Twinkle_Configuration(twinkleColors=twinkleColors, twinkleChance=twinkleChance)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Merge_Sequence_TrueRandomColors(self, refreshDelay=0.1, randomColorCount=None, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(2,6)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.trueRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.ReflectArray(arrayLength=self._LEDCount, colorSequence=colorSequence))
			self._Merge_Configuration(segmentLength=(self._LEDCount // 2))
			self._Twinkle_Configuration(twinkleColors=twinkleColors, twinkleChance=twinkleChance)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Merge_Rainbow(self, refreshDelay=0.1, segmentLength:int=None, arrayLength:int=None, backgroundColor=PixelColors.OFF, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Even More Different Do_Shift_Rainbow!
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount
			if segmentLength is None:
				segmentLength = self._LEDCount // 4
			ledArray = LightPattern.PixelArray(segmentLength * 2)
			ledArray[:segmentLength] = LightPattern.RainbowArray(arrayLength=segmentLength)
			ledArray = LightPattern.ReflectArray(self._LEDCount, ledArray)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=ledArray)
			self._Merge_Configuration(segmentLength=self._VirtualLEDCount // 2)
			self._Twinkle_Configuration(twinkleColors=twinkleColors, twinkleChance=twinkleChance)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Merge_Wintergreen(self, refreshDelay=0.01, backgroundColor=PixelColors.WHITE, twinkleColors:List[Pixel]=[DEFAULT_TWINKLE_COLOR], twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			segmentLength = self._LEDCount//2
			arry = LightPattern.SolidColorArray(segmentLength, backgroundColor)
			arry[0] = np.array(PixelColors.TEAL.tuple)
			arry[1] = np.array(PixelColors.TEAL.tuple)
			arry[2] = np.array(PixelColors.TEAL.tuple)
			arry = LightPattern.ConvertPixelArrayToNumpyArray(arry)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.ReflectArray(self._LEDCount, arry))
			self._Merge_Configuration(segmentLength=segmentLength)
			self._Twinkle_Configuration(twinkleColors=twinkleColors, twinkleChance=twinkleChance)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Merge_Configuration(self, segmentLength=20):
		"""
		splits the array into sections and shifts each section in the opposite direction

		Parameters:
			segmentLength: int
				the length of the segments to split the array into
		"""
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._MergeLength = segmentLength
			self._FunctionList.append(self._Merge_Function)
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
			segmentCount = (self._VirtualLEDIndexCount // self._MergeLength)
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


	def Do_Accelerate_Sequence(self, delaySteps=25, beginDelay=0.1, endDelay=0.001, colorSequence:List[Pixel]=[PixelColors.GREEN, PixelColors.GREEN, PixelColors.GREEN, PixelColors.RED, PixelColors.RED, PixelColors.RED, PixelColors.WHITE, PixelColors.WHITE, PixelColors.WHITE], backgroundColor=PixelColors.OFF):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			ledArray = LightPattern.PixelArray(self._LEDCount)
			ledArray[:len(colorSequence)] = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			self._Initialize(refreshDelay=beginDelay, backgroundColor=backgroundColor, ledArray=ledArray)
			self._Accelerate_Configuration(shift=1, beginDelay=beginDelay, endDelay=endDelay, delaySteps=delaySteps)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Accelerate_Sequence_RandomColors(self, delaySteps=25, beginDelay=0.1, endDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(2,6)
			colorSequence = []
			ledArray = LightPattern.ConvertPixelArrayToNumpyArray(LightPattern.PixelArray(arrayLength=self._LEDCount + randomColorCount+2))
			for i in range(randomColorCount):
				ledArray[i] = PixelColors.random().array
			self._Initialize(refreshDelay=beginDelay, backgroundColor=backgroundColor, ledArray=ledArray)
			self._Accelerate_Configuration(shift=1, beginDelay=beginDelay, endDelay=endDelay, delaySteps=delaySteps)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Accelerate_Sequence_TrueRandomColors(self, delaySteps=25, beginDelay=0.1, endDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = self._VirtualLEDCount // random.randint(2,6)
			colorSequence = []
			ledArray = LightPattern.ConvertPixelArrayToNumpyArray(LightPattern.PixelArray(arrayLength=self._LEDCount + randomColorCount+2))
			for i in range(randomColorCount):
				ledArray[i] = PixelColors.trueRandom().array
			self._Initialize(refreshDelay=beginDelay, backgroundColor=backgroundColor, ledArray=ledArray)
			self._Accelerate_Configuration(shift=1, beginDelay=beginDelay, endDelay=endDelay, delaySteps=delaySteps)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Accelerate_Rainbow(self, segmentLength:int=None, arrayLength:int=None, delaySteps:int=25, beginDelay:float=0.1, endDelay:float=0.001, backgroundColor=PixelColors.OFF, twinkleColor:Pixel=DEFAULT_TWINKLE_COLOR, twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Even More Different Do_Shift_Rainbow!
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount
			if segmentLength is None:
				segmentLength = 20
			# self.Do_Accelerate_Sequence(delaySteps=delaySteps, beginDelay=beginDelay, endDelay=endDelay, colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength))
			self._Initialize(refreshDelay=beginDelay, backgroundColor=backgroundColor, ledArray=LightPattern.RainbowArray(arrayLength=segmentLength))
			self._Accelerate_Configuration(shift=1, beginDelay=beginDelay, endDelay=endDelay, delaySteps=delaySteps)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Accelerate_Wes1(self, delaySteps=25, beginDelay=0.1, endDelay=0.001, backgroundColor=PixelColors.OFF):
		"""
		Wes chose the pattern
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			# self.Do_Accelerate_Sequence(delaySteps=delaySteps, beginDelay=beginDelay, endDelay=endDelay, colorSequence=LightPattern.WesArray())
			self._Initialize(refreshDelay=beginDelay, backgroundColor=backgroundColor, ledArray=LightPattern.WesArray())
			self._Accelerate_Configuration(shift=1, beginDelay=beginDelay, endDelay=endDelay, delaySteps=delaySteps)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Accelerate_Configuration(self, shift=1, beginDelay=0.3, endDelay=0.05, delaySteps=15):
		"""
		incrementally decreases the amount of self.RefreshDelay between each shift
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
			self._ShiftAmount=1
			self._BeginDelay=beginDelay
			self._EndDelay=endDelay
			self._DelaySteps=delaySteps
			self._DelayRange = np.log(np.linspace(np.e, 1, self._DelaySteps)) * (self._BeginDelay - self._EndDelay) + self._EndDelay
			if self._DelaySteps < self._VirtualLEDIndexCount:
				self._DelayRange = np.concatenate((self._DelayRange, np.ones(self._VirtualLEDIndexCount - self._DelaySteps) * self._EndDelay))
			self._AccelerateIndex = 0
			self._FunctionList.append(self._Accelerate_Function)
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
			self._AccelerateIndex += 1
			if self._AccelerateIndex >= len(self._DelayRange):
				self._AccelerateIndex = 0
			self.RefreshDelay = self._DelayRange[self._AccelerateIndex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_RandomChange_Sequence(self, refreshDelay=0.05, arrayLength:int=None, changeChance:float=None, colorSequence:List[Pixel]=[PixelColors.RED, PixelColors.GREEN, PixelColors.WHITE]):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount
			if changeChance is None:
				changeChance = 0.01
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RandomArray(arrayLength=arrayLength))
			self._RandomChange_Configuration(changeChance=changeChance, colorSequence=colorSequence)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChange_RandomColors(self, refreshDelay=0.05, arrayLength:int=None, changeChance:float=None):
		"""
		It's very blinky
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount
			if changeChance is None:
				changeChance = 0.01
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RandomArray(arrayLength=arrayLength))
			self._RandomChange_Configuration(changeChance=changeChance, colorSequence=PixelColors.random)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChange_TrueRandomColors(self, refreshDelay=0.05, arrayLength:int=None, changeChance:float=None):
		"""
		It's very blinky
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount
			if changeChance is None:
				changeChance = 0.01
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.TrueRandomArray(arrayLength=arrayLength))
			self._RandomChange_Configuration(changeChance=changeChance, colorSequence=PixelColors.trueRandom)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChange_Configuration(self, changeChance, colorSequence):
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
			self.ColorSequence = colorSequence
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
					self._VirtualLEDArray[LEDIndex] = self.ColorSequenceNext
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_RandomChangeFade_Sequence(self, refreshDelay=0.05, colorSequence=[PixelColors.RED,PixelColors.RED,PixelColors.GREEN,PixelColors.GREEN], fadeInChance=0.25, backgroundColor=PixelColors.WHITE, fadeStepCount=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._RandomChangeFade_Configuration(fadeInChance, fadeStepCount, colorSequence)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChangeFade_RandomColors(self, refreshDelay=0.001, randomColorCount=None, fadeInChance=0.1, backgroundColor=PixelColors.WHITE, fadeStepCount=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			colorSequence = PixelColors.random
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._RandomChangeFade_Configuration(fadeInChance, fadeStepCount, colorSequence)
			self.ColorSequenceCount = randomColorCount
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_RandomChangeFade_TrueRandomColors(self, refreshDelay=0.001, randomColorCount=None, fadeInChance=0.1, backgroundColor=PixelColors.WHITE, fadeStepCount=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			colorSequence = PixelColors.trueRandom
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._RandomChangeFade_Configuration(fadeInChance, fadeStepCount, colorSequence)
			self.ColorSequenceCount = randomColorCount
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChangeFade_Configuration(self, fadeInChance, fadeStepCount, colorSequence):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeChance = fadeInChance
			self._FadeStepCount = fadeStepCount
			self._FadeAmount = 255 // self._FadeStepCount
			self._FadeStepCounter = 0
			self._PreviousIndices = np.array([])
			self.ColorSequence = colorSequence
			self._FunctionList.append(self._RandomChangeFade_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _RandomChangeFade_Function(self):
		try:
			if self._FadeStepCounter == 0:
				temp = []
				for i in range(self.ColorSequenceCount):
					temp.append(self.ColorSequenceNext)
				self.ColorSequence = temp
				self._DefaultColorIndices = list(range(self._VirtualLEDCount))
				self._FadeInColorIndices = []
				for color in self.ColorSequence:
					self._FadeInColorIndices.append(self._GetRandomIndices(self._FadeChance))
				for colorListIndex in range(len(self._FadeInColorIndices)):
					for colorIndex in self._FadeInColorIndices[colorListIndex]:
						x = np.intersect1d(self._FadeInColorIndices[colorListIndex], self._PreviousIndices)
						self._FadeInColorIndices[colorListIndex] = [i for i in self._FadeInColorIndices[colorListIndex] if not i in x]
						x = np.intersect1d(self._FadeInColorIndices[colorListIndex], self._DefaultColorIndices)
						self._DefaultColorIndices = [i for i in self._DefaultColorIndices if not i in x]
						if colorListIndex > 1:
							previousColorIndex = colorListIndex -1
							x = np.intersect1d(self._FadeInColorIndices[colorListIndex], self._FadeInColorIndices[previousColorIndex])
							self._FadeInColorIndices[colorListIndex] = [i for i in self._FadeInColorIndices[colorListIndex] if not i in x]
			for colorIndex in range(len(self._FadeInColorIndices)):
				self._ModifyFade(color=self.ColorSequence[colorIndex],fadeIndices=self._FadeInColorIndices[colorIndex],step=self._FadeAmount)
			self._FadeStepCounter += 1
			if self._FadeStepCounter >= self._FadeStepCount:
				self._PreviousIndices = []
				for colorIndexList in self._FadeInColorIndices:
					self._PreviousIndices.extend(colorIndexList)
				self._FadeStepCounter = 0

		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Meteors_Sequence(self, refreshDelay=0.01, arrayLength=None, colorSequence=[PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.RED], backgroundColor=PixelColors.OFF, fadeAmount=0.25, maxSpeed=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount*1.2
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=arrayLength, color=backgroundColor))
			self._Meteors_Configuration(colorSequence=colorSequence, fadeAmount=0.25, maxSpeed=2)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Meteors_RandomColors(self, refreshDelay=0.01, arrayLength=None, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=0.25, maxSpeed=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount*1.2
			if randomColorCount is None:
				randomColorCount = random.randint(1,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=arrayLength, color=backgroundColor))
			self._Meteors_Configuration(colorSequence=colorSequence, fadeAmount=0.25, maxSpeed=2)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Meteors_TrueRandomColors(self, refreshDelay=0.01, arrayLength=None, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=0.25, maxSpeed=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._LEDCount*1.2
			if randomColorCount is None:
				randomColorCount = random.randint(1,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.trueRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=arrayLength, color=backgroundColor))
			self._Meteors_Configuration(colorSequence=colorSequence, fadeAmount=0.25, maxSpeed=2)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Configuration(self, colorSequence, fadeAmount=0.25, maxSpeed=2):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			for index, color in enumerate(colorSequence):
				meteor = LightData(color)
				meteor.index = random.randint(0,self._VirtualLEDIndexCount-1)
				meteor.step = (-maxSpeed,maxSpeed)[random.randint(0,1)]
				while meteor.step == 0:
					meteor.step = random.randint(-maxSpeed,maxSpeed)
				meteor.stepCountMax = random.randint(2, self._VirtualLEDIndexCount-1)
				meteor.colorSequenceIndex = index
				self._LightDataObjects.append(meteor)
			self._FadeAmount = int(255 * fadeAmount)
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
					if self._VirtualLEDArray[ledIndex][rgbIndex] - self._FadeAmount >= self.BackgroundColor.tuple[rgbIndex]:
						self._VirtualLEDArray[ledIndex][rgbIndex] -= self._FadeAmount
					elif self._VirtualLEDArray[ledIndex][rgbIndex] + self._FadeAmount <= self.BackgroundColor.tuple[rgbIndex]:
						self._VirtualLEDArray[ledIndex][rgbIndex] += self._FadeAmount
					else:
						self._VirtualLEDArray[ledIndex][rgbIndex] = self.BackgroundColor.tuple[rgbIndex]
			for meteor in self._LightDataObjects:
				newLocation = (meteor.index + meteor.step) % self._VirtualLEDIndexCount
				meteor.index = newLocation
				meteor.stepCounter += 1
				if meteor.stepCounter >= meteor.stepCountMax:
					meteor.stepCounter = 0
					meteor.step = (-self._MaxSpeed, self._MaxSpeed)[random.randint(0,1)]
					meteor.stepCountMax = random.randint(2,self._VirtualLEDIndexCount*2)

				self._VirtualLEDArray[meteor.index] = meteor.colors[meteor.colorindex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_MeteorsFancy_Sequence(self, refreshDelay=0.03, colorSequence=[PixelColors.WHITE, PixelColors.WHITE, PixelColors.RED, PixelColors.RED, PixelColors.GREEN], meteorCount=3, backgroundColor=PixelColors.OFF, fadeAmount=35, maxSpeed=2, cycleColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsFancy_Configuration(meteorCount=meteorCount, colorSequence=colorSequence, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsFancy_RandomColors(self, refreshDelay=0.03, randomColorCount=None, meteorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=35, maxSpeed=2, cycleColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if meteorCount is None:
				meteorCount = random.randint(1,7)
			if randomColorCount is None:
				randomColorCount = random.randint(3,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsFancy_Configuration(meteorCount=meteorCount, colorSequence=colorSequence, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsFancy_TrueRandomColors(self, refreshDelay=0.03, randomColorCount=None, meteorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=35, maxSpeed=2, cycleColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if meteorCount is None:
				meteorCount = random.randint(1,7)
			if randomColorCount is None:
				randomColorCount = random.randint(3,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.trueRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsFancy_Configuration(meteorCount=meteorCount, colorSequence=colorSequence, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsFancy_Configuration(self, meteorCount, colorSequence, maxSpeed, fadeAmount, cycleColors):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._MeteorCount = meteorCount
			self.ColorSequence = colorSequence
			self._FadeAmount = fadeAmount
			self._CycleColors = cycleColors
			self._MaxSpeed = maxSpeed
			for i in range(self._MeteorCount):
				meteor = LightData(self.ColorSequence[::-1])
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


	def Do_MeteorsBouncy_Sequence(self, refreshDelay=0.001, colorSequence=[PixelColors.WHITE, PixelColors.GREEN, PixelColors.RED], backgroundColor=PixelColors.OFF, fadeAmount=25, maxSpeed=1, explode=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			temp = np.copy(colorSequence)
			while len(temp) < 3:
				temp = np.concatenate((temp, colorSequence))
			colorSequence = temp
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsBouncy_Configuration(colorSequence=colorSequence, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsBouncy_RandomColors(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=25, maxSpeed=1, explode=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(3,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.random())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsBouncy_Configuration(colorSequence=colorSequence, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_MeteorsBouncy_TrueRandomColors(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=25, maxSpeed=1, explode=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(3,7)
			colorSequence = []
			for i in range(randomColorCount):
				colorSequence.append(PixelColors.trueRandom())
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=backgroundColor))
			self._MeteorsBouncy_Configuration(colorSequence=colorSequence, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _MeteorsBouncy_Configuration(self, colorSequence, fadeAmount, maxSpeed, explode):
		try:
			LOGGER.log(5, '%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.ColorSequence = colorSequence
			self._FadeAmount = fadeAmount
			self._MaxSpeed = maxSpeed
			self._Explode = explode
			for index, color in enumerate(self.ColorSequence):
				meteor = LightData(color)
				meteor.index = random.randint(0, self._VirtualLEDCount -1)
				meteor.previousIndex = meteor.index
				meteor.step = (-maxSpeed, maxSpeed)[random.randint(0,1)]
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
								meteor1.bounce = True
								meteor2.bounce = True
								foundBounce = True
			# handle collision of self._LightDataObjects
			explosions=[]
			if foundBounce == True:
				for index, meteor in enumerate(self._LightDataObjects):
					if meteor.bounce:
						previous = int(meteor.step)
						meteor.step = (-self._MaxSpeed, self._MaxSpeed)[random.randint(0,1)]
						if meteor.step * previous > 0:
							meteor.step *= -1
						newLocation = (meteor.index + meteor.step) % self._VirtualLEDCount
						meteor.index = newLocation + random.randint(0,3)
						meteor.previousIndex = newLocation
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
					self._VirtualLEDArray[meteor.index] = meteor.colors[meteor.colorindex]
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


	def Do_MeteorsAgain_Sequence(self, refreshDelay=0.001, colorSequence=[PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN], backgroundColor=PixelColors.OFF, maxDelay=5, fadeSteps=25, randomColors=True):
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

	def Do_MeteorsAgain_RandomColors(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=5, fadeSteps=25, randomColors=True):
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

	def Do_MeteorsAgain_TrueRandomColors(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=5, fadeSteps=25, randomColors=True):
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
				colorSequence.append(PixelColors.trueRandom())
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
			self.ColorSequence = colorSequence
			self._MaxDelay = maxDelay
			self._FadeAmount = fadeAmount
			self._FadeSteps = fadeSteps
			for index, color in enumerate(self.ColorSequence):
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
				self._FadeLED(ledIndex, self.BackgroundColor, self._FadeAmount/2)
			for meteor in self._LightDataObjects:
				self._VirtualLEDArray[meteor.index] = meteor.colors[meteor.colorindex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Paint_Sequence(self, refreshDelay=0.001, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE,PixelColors.OFF], backgroundColor=PixelColors.OFF, maxDelay=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.BackgroundColor))
			self._Paint_Configuration(randomColors=False, colorSequence=colorSequence, colorCount=len(colorSequence), maxDelay=maxDelay)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Paint_RandomColors(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=10, randomColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.BackgroundColor))
			self._Paint_Configuration(randomColors=True, colorSequence=PixelColors.random, colorCount=randomColorCount, maxDelay=maxDelay)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Paint_TrueRandomColors(self, refreshDelay=0.001, randomColorCount=None, backgroundColor=PixelColors.OFF, maxDelay=10, randomColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.BackgroundColor))
			self._Paint_Configuration(randomColors=True, colorSequence=PixelColors.trueRandom, colorCount=randomColorCount, maxDelay=maxDelay)
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
			self.ColorSequence = colorSequence
			self._MaxDelay = maxDelay
			for i in range(colorCount):
				paintBrush = LightData(self.ColorSequenceNext)
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
							paintBrush.colors = [self.ColorSequenceNext]
				self._VirtualLEDArray[paintBrush.index] = paintBrush.colors[paintBrush.colorindex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Sprites_Sequence(self, refreshDelay=0.03, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE], backgroundColor=PixelColors.OFF, fadeAmount=15):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.BackgroundColor))
			self._Sprites_Configuration(fadeAmount=fadeAmount, colorSequence=colorSequence, colorCount=len(colorSequence), randomColors=False)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Sprites_RandomColors(self, refreshDelay=0.03, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.BackgroundColor))
			self._Sprites_Configuration(fadeAmount=fadeAmount, colorSequence=PixelColors.random, colorCount=randomColorCount, randomColors=True)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Sprites_TrueRandomColors(self, refreshDelay=0.03, randomColorCount=None, backgroundColor=PixelColors.OFF, fadeAmount=10):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._LEDCount, color=self.BackgroundColor))
			self._Sprites_Configuration(fadeAmount=fadeAmount, colorSequence=PixelColors.trueRandom, colorCount=randomColorCount, randomColors=True)
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
			self.ColorSequence = colorSequence
			for i in range(colorCount):
				sprite = LightData(self.ColorSequenceNext)
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
								self._VirtualLEDArray[sprite.index] = sprite.colors[sprite.colorindex]
								if not first:
									self._FadeLED(index, self.BackgroundColor, self._FadeAmount)
								first - False
							#sprite[sprite_index] = ma
						else:
							for index in range(ma-1, mi-1,-1):
								index = index % self._VirtualLEDCount
								sprite.index = index
								self._VirtualLEDArray[sprite.index] = sprite.colors[sprite.colorindex]
								if not first:
									self._FadeLED(index, self.BackgroundColor, self._FadeAmount)
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
							sprite.colors = [self.ColorSequenceNext]
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


	def Dont_Spaz(self, refreshDelay=0.02, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE], twinkleColors=[PixelColors.CYAN], blinkColors=[PixelColors.OFF, PixelColors.WHITE], shiftAmount=7, twinkleChance=0.5, blinkChance=0.5):
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


	def Do_Raindrops_Sequence(self, refreshDelay=0.05, colorSequence=[PixelColors.RED, PixelColors.GREEN, PixelColors.WHITE], maxSize=15, backgroundColor=PixelColors.OFF, fadeAmount=25):
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

	def Do_Raindrops_RandomColors(self, refreshDelay=0.05, randomColorCount=None, maxSize=15, backgroundColor=PixelColors.OFF, fadeAmount=25):
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

	def Do_Raindrops_TrueRandomColors(self, refreshDelay=0.05, randomColorCount=None, maxSize=15, backgroundColor=PixelColors.OFF, fadeAmount=25):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if randomColorCount is None:
				randomColorCount = random.randint(2,5)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			self._Raindrops_Configuration(colorSequence=PixelColors.trueRandom, colorCount=randomColorCount, fadeAmount=fadeAmount, maxSize=maxSize, randomColors=True)
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
			self.ColorSequence = colorSequence
			for i in range(colorCount):
				raindrop = LightData(self.ColorSequenceNext)
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
						self._VirtualLEDArray[(raindrop.index + raindrop.stepCounter) % self._VirtualLEDCount] = raindrop.colors[raindrop.colorindex]
						self._VirtualLEDArray[(raindrop.index - raindrop.stepCounter)] = raindrop.colors[raindrop.colorindex]
						raindrop.colors[raindrop.colorindex] = self._FadeColor(raindrop.colors[raindrop.colorindex], fadeAmount=raindrop.fadeAmount)
						raindrop.stepCounter += 1
					else:
						raindrop.index = random.randint(0, self._VirtualLEDCount-1)
						raindrop.stepCountMax = random.randint(2, raindrop.maxSize//2)
						raindrop.fadeAmount = 192 // raindrop.stepCountMax
						raindrop.stepCounter = 0
						raindrop.colors = [self.ColorSequenceNext]
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
			self.SecondsPerMode = secondsPerMode
			funcs = list(dir(self))
			funcs = [f  for f in funcs if f.lower()[:3] == 'do_']
			while True:
				getattr(self, funcs[random.randint(0, len(funcs)-1)])()
		except SystemExit:
			pass
		except KeyboardInterrupt:
			pass
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

class LightData():
	def __init__(self, colors):
		self.index = 0
		self.lastindex = 0
		self.step = 0
		self.stepCounter = 0
		self.stepCountMax = 0
		self.previousIndex = 0
		self.moveRange = 0
		self.bounce = False
		self.delayCounter = 0
		self.delayCountMax = 0
		self.active = 0
		self.activeChance = 0
		self.duration = 0
		self.direction = 0
		self.colorSequenceIndex = 0
		self.maxSize = 0
		self.fadeAmount = 0
		self.colorindex = 0
		self.random = False
		if hasattr(colors, '__len__') and hasattr(colors, 'shape') and len(colors.shape)>1:
			self.colors = LightPattern.ConvertPixelArrayToNumpyArray(colors)
		else:
			self.colors = np.array([Pixel(colors).tuple])

if __name__ == '__main__':
	try:
		from LightStrings import LightString
		ws281x = rpi_ws281x.Adafruit_NeoPixel(pin=18, dma=5, num=ledCount, freq_hz=800000)
		lights = LightString(rpi_ws281x=ws281x)
		func = LightFunction(lights=lights, debug=True)
		func.demo(0.2)
	except KeyboardInterrupt:
		pass
	except SystemExit:
		pass