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
	def __init__(self, lights=LightString(), debug=False, verbose=False):
		try:
			self._WS281xLights = lights
			if True == debug:
				LOGGER.setLevel(logging.DEBUG)
			if True == verbose:
				LOGGER.setLevel(5)
				self._WS281xLights.setDebugLevel(5)
			self._WS281xLightCount = len(self._WS281xLights)
			self._VirtualLEDArray = LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=PixelColors.OFF)
			self._VirtualLEDBuffer = np.copy(self._VirtualLEDArray)
			self._VirtualLEDCount = len(self._VirtualLEDArray)
			self._VirtualLEDIndexArray = np.array(range(len(self._WS281xLights)))
			self._VirtualLEDIndexCount = len(self._VirtualLEDIndexArray)
			self._LastModeChange = None
			self._NextModeChange = None
			self._FunctionList = []

			self.__RefreshDelay = 0.001
			self.__SecondsPerMode = 120
			self.__BackgroundColor = PixelColors.OFF
			self.__ColorSequence = LightPattern._FixColorSequence([])

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
			self._ColorSequenceCount = 0
			self._ColorSequenceIndex = 0
			self._FadeAmount = 0
		except Exception as ex:
			LOGGER.error('{}.__Initialize__() Failed: {}'.format('LightFunction', ex))
			raise

	def __del__(self):
		try:
			if not self._WS281xLights is None:
				del(self._WS281xLights)
				self._WS281xLights = None
		except Exception as ex:
			LOGGER.error('{}.__del__() Failed: {}'.format('LightFunction', ex))
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
		self.__ColorSequence = LightPattern._FixColorSequence(colorSequence)

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
		except Exception as ex:
			LOGGER.error('{}._Initialize() Failed: {}'.format('LightFunction', ex))
			raise

	def _SetVirtualLEDArray(self, ledArray:List[List[int]]) -> None:
		"""
		"""
		try:
			if ledArray is None:
				self._VirtualLEDArray = LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=self.BackgroundColor)
			else:
				self._VirtualLEDArray = LightPattern._FixColorSequence(ledArray)
			# assign new LED array to virtual LEDs
			self._VirtualLEDBuffer = np.copy(self._VirtualLEDArray)
			self._VirtualLEDCount = len(self._VirtualLEDArray)
			# set our indices for virtual LEDs
			self._VirtualLEDIndexCount = self._VirtualLEDCount
			self._VirtualLEDIndexArray = np.array(range(self._VirtualLEDIndexCount))
			# if the array is smaller than the actual light strand, make our entire strand addressable
			if self._VirtualLEDIndexCount < self._WS281xLightCount:
				self._VirtualLEDIndexCount = self._WS281xLightCount
				self._VirtualLEDIndexArray = np.array(range(self._VirtualLEDIndexCount))
				self._VirtualLEDArray = np.concatenate((self._VirtualLEDArray, np.array([PixelColors.OFF.value.Tuple for i in range(self._WS281xLightCount - len(self._VirtualLEDArray))])))
		except Exception as ex:
			LOGGER.error('{}._SetVirtualLEDArray Failed: {}'.format('LightFunction', ex))
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
			self._WS281xLights[:] = [led_array[self._VirtualLEDIndexArray[i]] for i in range(self._WS281xLightCount)]
		except Exception as ex:
			print('_CopyVirtualLedsToWS281X',ex)
			raise

	def _RefreshLEDs(self):
		"""
		Display current LED NeoPixel buffer
		"""
		#if self.verbose:
		#    print(('_RefreshLEDs', self._WS281xLightCount)
		self._WS281xLights.Refresh()

	def _RunFunctions(self):
		for function in self._FunctionList:
			function()

	def _RunOverlays(self):
		#if self.verbose:
		#    print('_RunOverlays: overlay count={}'.format(len(self._OverlayList)))
		for overlay in self._OverlayList:
			overlay()

	def _GetRandomIndices(self, getChance=0.1):
		maxVal = 1000
		temp = []
		for LEDIndex in range(self._VirtualLEDCount):
			doLight = random.randint(0, maxVal)
			if doLight > maxVal * (1.0 - getChance):
				temp.append(LEDIndex)
		return temp

	def _Fade(self):
		'''
		'''
		[self._FadeLED(i, self.BackgroundColor, self._FadeAmount) for i in range(len(self._VirtualLEDArray))]

	def _FadeLED(self, led_index, offColor=None, fadeAmount=None):
		if offColor is None:
			offColor = self.BackgroundColor
		if fadeAmount is None:
			fadeAmount = self._FadeAmount
		offColor = Pixel(offColor).Array
		self._VirtualLEDArray[led_index] = self._FadeColor(self._VirtualLEDArray[led_index], offColor, fadeAmount)

	def _FadeColor(self, color, offColor=None, fadeAmount=None):
		if offColor is None:
			offColor = self.BackgroundColor
		if fadeAmount is None:
			fadeAmount = self._FadeAmount
		color = Pixel(color).Array
		offColor = Pixel(offColor).Array
		for rgbIndex in range(len(color)):
			if color[rgbIndex] != offColor[rgbIndex]:
				if color[rgbIndex] - fadeAmount > offColor[rgbIndex]:
					color[rgbIndex] -= fadeAmount
				elif color[rgbIndex] + fadeAmount < offColor[rgbIndex]:
					color[rgbIndex] += fadeAmount
				else:
					color[rgbIndex] = offColor[rgbIndex]
		return color

	def _Run(self):
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



	# def GetRandomColorSequence(self, color_sequence, do_random, color_count, user_sequence):
	# 	print(user_sequence)
	# 	if not user_sequence is None:
	# 		color_sequence = user_sequence
	# 	if do_random:
	# 		color_sequence = []
	# 		for i in range(color_count):
	# 			keys = list(COLORS_NO_OFF.keys())
	# 			new_color=COLORS_NO_OFF[keys[random.randint(0,len(keys)-1)]]
	# 			if len(color_sequence) > i:
	# 				color_sequence[i] = new_color
	# 			else:
	# 				color_sequence.append(new_color)
	# 	return color_sequence



	def Do_SolidColor(self, refreshDelay=0.5, backgroundColor=PixelColors.WHITE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=backgroundColor))
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_SolidColor_Random(self, refreshDelay=0.5):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			backgroundColor = PixelColors.RANDOM()
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=backgroundColor))
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_SolidColor_Cycle_Sequence(self, refreshDelay=0.5, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE]):
		"""
		For dad
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=None)
			self._Cycle_Configuration(colorSequence=colorSequence)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_SolidColor_Cycle_Rainbow(self, refreshDelay=0.5, segmentLength=75):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.Do_SolidColor_Cycle_Sequence(refreshDelay=refreshDelay, colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength))
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.ColorSequence = colorSequence
			self._ColorSequenceCount = len(self.ColorSequence)
			self._ColorSequenceIndex = 0
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
			self._VirtualLEDArray += self.ColorSequence[self._ColorSequenceIndex]
			self._ColorSequenceIndex += 1
			if self._ColorSequenceIndex >= self._ColorSequenceCount:
				self._ColorSequenceIndex = 0
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
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=colorSequence)
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

	def Do_Shift_SequenceRepeating(self, refreshDelay=0.1, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], backgroundColor=PixelColors.OFF, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE, shiftAmount=1):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._WS281xLightCount / len(colorSequence)) * len(colorSequence)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence))
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

	def Do_Shift_Rainbow(self, refreshDelay=0.1, rainbowLength=None, twinkleColors=[DEFAULT_TWINKLE_COLOR], twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		RainbowChases! Unicorns!
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if rainbowLength is None:
				rainbowLength = self._WS281xLightCount
			self.Do_Shift_Sequence(refreshDelay=refreshDelay, colorSequence=LightPattern.RainbowArray(arrayLength=rainbowLength), twinkleColors=twinkleColors, twinkleChance=twinkleChance)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Emily1(self, refreshDelay=0.1):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.Do_Shift_Sequence(refreshDelay=refreshDelay, colorSequence=LightPattern.Emily1())
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Shift_Lily1(self):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.Do_Shift_Sequence(colorSequence=LightPattern.ColorStretchArray())
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
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
		'''
		'''
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
			colorSequence = LightPattern._FixColorSequence(colorSequence)
			sequenceLength = len(colorSequence)
			while len(colorSequence) < self._WS281xLightCount:
				colorSequence = np.concatenate((colorSequence, colorSequence), 0)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=colorSequence)
			self._Shift_Fade_Configuration(shiftAmount=shiftAmount, fadeStepCount=fadeStepCount)
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
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


	def Do_Alternate_Sequence(self, refreshDelay=0.05, shiftAmount=1, shiftCount=None, flipLength=None, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], twinkleColor=DEFAULT_TWINKLE_COLOR, twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._WS281xLightCount / len(colorSequence)) * len(colorSequence)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=colorSequence))
			self._Alternate_Configuration(shiftAmount=1, shiftCount=len(colorSequence), flipLength=flipLength)
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Alternate_Rainbow(self, refreshDelay=0.05, segmentLength:int=None, arrayLength:int=None, twinkleColor:Pixel=DEFAULT_TWINKLE_COLOR, twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if segmentLength is None:
				segmentLength = 20
			if arrayLength is None:
				arrayLength = self._WS281xLightCount
			self.Do_Alternate_Sequence(refreshDelay=refreshDelay, colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength), twinkleColor=twinkleColor, twinkleChance=twinkleChance)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Alternate_CylonEye(self, refreshDelay=0.01, eyeColor=PixelColors.RED, backgroundColor=PixelColors.OFF):
		"""
		C Y L O N E Y E
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			ledArray = LightPattern._PixelArray(arrayLength=self._WS281xLightCount)
			ledArray[0] = Pixel(eyeColor).Array
			self.Do_Alternate_Sequence(refreshDelay=refreshDelay, shiftAmount=1, shiftCount=None, flipLength=None, colorSequence=ledArray)
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Alternate_Configuration(self, shiftAmount:int, shiftCount:int, flipLength:int):
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if shiftCount is None:
				shiftCount = (self._VirtualLEDCount - 1)
			self._ShiftAmount = shiftAmount
			self._ShiftCount = shiftCount
			self._ShiftCounter = 0
			self._flipLength = flipLength
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


	def Do_BetterCylon(self, refreshDelay=0.01, colorSequence=[PixelColors.RED], backgroundColor=PixelColors.OFF, fadeAmount=15, cylonSpeedup=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=backgroundColor))
			self._BetterCylon_Configuration(refreshDelay, colorSequence, fadeAmount, cylonSpeedup)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _BetterCylon_Configuration(self,refreshDelay, colorSequence, fadeAmount, cylonSpeedup):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.ColorSequence = colorSequence
			for index, color in enumerate(self.ColorSequence):
				eye = LightData(color)
				eye.step = 3
				eye.direction=1
				eye.colorSequenceIndex = index
				self._LightDataObjects.append(eye)
			self._FadeAmount = fadeAmount
			self._CylonSpeedup = cylonSpeedup
			self._FunctionList.append(self._BetterCylon_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _BetterCylon_Function(self):
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


	def Do_Merge_Sequence(self, refreshDelay=0.1, colorSequence=[PixelColors.RED, PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN, PixelColors.GREEN, PixelColors.WHITE], twinkleColor=DEFAULT_TWINKLE_COLOR, twinkleChance=DEFAULT_TWINKLE_CHANCE):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arrayLength = np.ceil(self._WS281xLightCount / len(colorSequence)) * len(colorSequence)
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.ReflectArray(arrayLength=arrayLength, colorSequence=colorSequence))
			self._Merge_Configuration(segmentLength=len(colorSequence))
			self._Run()
		except KeyboardInterrupt:
			raise
		except SystemExit:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Merge_Rainbow(self, refreshDelay=0.1, segmentLength:int=None, arrayLength:int=None, twinkleColor:Pixel=DEFAULT_TWINKLE_COLOR, twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Even More Different Do_Shift_Rainbow!
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._WS281xLightCount
			if segmentLength is None:
				segmentLength = 20
			self.Do_Merge_Sequence(refreshDelay=refreshDelay, colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength), twinkleColor=twinkleColor, twinkleChance=twinkleChance)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Merge_Wintergreen(self):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			arry = LightPattern.SolidColorArray(50,PixelColors.WHITE)
			arry[0] = np.array(PixelColors.TEAL.value.Tuple)
			arry[1] = np.array(PixelColors.TEAL.value.Tuple)
			arry[2] = np.array(PixelColors.TEAL.value.Tuple)
			arry = LightPattern._FixColorSequence(arry)
			self.Do_Merge_Sequence(refreshDelay=0.01, colorSequence=arry)
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
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
			ledArray = LightPattern._PixelArray(self._WS281xLightCount)
			ledArray[:len(colorSequence)] = LightPattern._FixColorSequence(colorSequence)
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

	def Do_Accelerate_Rainbow(self, segmentLength:int=None, arrayLength:int=None, delaySteps:int=25, beginDelay:float=0.1, endDelay:float=0.001, twinkleColor:Pixel=DEFAULT_TWINKLE_COLOR, twinkleChance:float=DEFAULT_TWINKLE_CHANCE):
		"""
		Even More Different Do_Shift_Rainbow!
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._WS281xLightCount
			if segmentLength is None:
				segmentLength = 20
			self.Do_Accelerate_Sequence(delaySteps=delaySteps, beginDelay=beginDelay, endDelay=endDelay, colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength))
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def Do_Accelerate_Wes1(self, delaySteps=25, beginDelay=0.1, endDelay=0.001):
		"""
		Wes chose the pattern
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self.Do_Accelerate_Sequence(delaySteps=delaySteps, beginDelay=beginDelay, endDelay=endDelay, colorSequence=LightPattern.WesArray())
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
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


	def Do_Random_Change(self, refreshDelay=0.05, arrayLength:int=None, changeChance:float=None):
		"""
		It's very blinky
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._WS281xLightCount
			if changeChance is None:
				changeChance = 0.01
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.TrueRandomArray(arrayLength=arrayLength))
			self._Random_Change_Configuration(changeChance=changeChance)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Random_Change_Configuration(self, changeChance=0.05):
		"""
		Makes random changes to the LED array

		Parameters:
			changeChance: float
				a floating point number specifying the chance of
				modifying any given LED's value
		"""
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._RandomChangeChance = changeChance
			self._FunctionList.append(self._Random_Change_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Random_Change_Function(self):
		try:
			maxVal = 1000
			for LEDIndex in range(self._VirtualLEDIndexCount):
				doLight = random.randint(0, maxVal)
				if doLight > maxVal * (1.0 - self._RandomChangeChance):
					x = random.randint(0,2)
					if x != 0:
						redLED = random.randint(0,255)
					else:
						redLED = 0
					if x != 1:
						greenLED = random.randint(0,255)
					else:
						greenLED = 0
					if x != 2:
						blueLED = random.randint(0,255)
					else:
						blueLED = 0
					arry = [redLED, greenLED, blueLED]
					self._VirtualLEDArray[LEDIndex] = arry
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Random_Change_Fade(self, refreshDelay=0.05, colorSequence=[PixelColors.RED,PixelColors.RED,PixelColors.GREEN,PixelColors.GREEN], fadeInChance=0.25, backgroundColor=PixelColors.WHITE, fadeStepCount=15):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=backgroundColor))
			self._Random_Change_Fade_Configuration(fadeInChance, fadeStepCount, colorSequence)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Random_Change_Fade_Configuration(self, fadeInChance, fadeStepCount, colorSequence):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeChance = fadeInChance
			self._FadeStepCount = fadeStepCount
			self._FadeStepCounter = 0
			self._PreviousIndices = np.array([])
			self.ColorSequence = colorSequence
			self._FunctionList.append(self._Random_Change_Fade_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Random_Change_Fade_Function(self):
		try:
			if self._FadeStepCounter == 0:
				self._DefaultColorIndices = list(range(self._VirtualLEDCount))
				self._FadeInColorIndices = []
				for color in self.ColorSequence:
					self._FadeInColorIndices.append(self._GetRandomIndices(self._FadeChance))
				for colorListIndex in range(len(self._FadeInColorIndices)):
					for colorIndex in self._FadeInColorIndices[colorListIndex]:
						if colorIndex in self._PreviousIndices:
							self._FadeInColorIndices[colorListIndex].remove(colorIndex)
						if colorIndex in self._DefaultColorIndices:
							self._DefaultColorIndices.remove(colorIndex)
						if colorListIndex + 1 < len(self._FadeInColorIndices):
							for otherColorListIndex in range(colorListIndex+1,len(self._FadeInColorIndices)):
								if colorIndex in self._FadeInColorIndices[otherColorListIndex]:
									self._FadeInColorIndices[otherColorListIndex].remove(colorIndex)
			for colorIndex in range(len(self._FadeInColorIndices)):
				self._ModifyFade(color=self.ColorSequence[colorIndex],fadeIndices=self._FadeInColorIndices[colorIndex],step=(255//self._FadeStepCount))
			self._ModifyFade(color=self.BackgroundColor,fadeIndices=self._DefaultColorIndices,step=(255//self._FadeStepCount))
			self._FadeStepCounter += 1
			if self._FadeStepCounter >= self._FadeStepCount:
				self._PreviousIndices = np.array([])
				for colorIndexList in self._FadeInColorIndices:
					self._PreviousIndices = np.concatenate((self._PreviousIndices,colorIndexList))
				self._FadeStepCounter = 0
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Meteors(self, refreshDelay=0.01, arrayLength=None, colorSequence=[PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.RED], backgroundColor=PixelColors.OFF, fadeAmount=0.25, maxSpeed=2):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			if arrayLength is None:
				arrayLength = self._WS281xLightCount*1.2
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
			LOGGER.debug('Do_Meteors-Configuration')
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
					if self._VirtualLEDArray[ledIndex][rgbIndex] - self._FadeAmount >= self.BackgroundColor.Tuple[rgbIndex]:
						self._VirtualLEDArray[ledIndex][rgbIndex] -= self._FadeAmount
					elif self._VirtualLEDArray[ledIndex][rgbIndex] + self._FadeAmount <= self.BackgroundColor.Tuple[rgbIndex]:
						self._VirtualLEDArray[ledIndex][rgbIndex] += self._FadeAmount
					else:
						self._VirtualLEDArray[ledIndex][rgbIndex] = self.BackgroundColor.Tuple[rgbIndex]
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


	def Do_Meteors_Fancy(self, refreshDelay=0.03, colorSequence=[PixelColors.WHITE, PixelColors.WHITE, PixelColors.RED, PixelColors.RED, PixelColors.GREEN], meteorCount=3, backgroundColor=PixelColors.OFF, fadeAmount=35, maxSpeed=2, cycleColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=backgroundColor))
			self._Meteors_Fancy_Configuration(meteorCount=meteorCount, colorSequence=colorSequence, maxSpeed=maxSpeed, fadeAmount=fadeAmount, cycleColors=cycleColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Fancy_Configuration(self, meteorCount, colorSequence, maxSpeed, fadeAmount, cycleColors):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
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
			self._FunctionList.append(self._Meteors_Fancy_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Fancy_Function(self):
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


	def Do_Meteors_Bouncy(self, refreshDelay=0.001, colorSequence=[PixelColors.WHITE, PixelColors.GREEN, PixelColors.RED], backgroundColor=PixelColors.OFF, fadeAmount=25, maxSpeed=1, explode=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			colorSequence = LightPattern._FixColorSequence(colorSequence)
			temp = np.copy(colorSequence)
			while len(temp) < 3:
				temp = np.concatenate((temp, colorSequence))
			colorSequence = temp
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=backgroundColor))
			self._Meteors_Bouncy_Configuration(colorSequence=colorSequence, fadeAmount=fadeAmount, maxSpeed=maxSpeed, explode=explode)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Bouncy_Configuration(self, colorSequence, fadeAmount, maxSpeed, explode):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
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
			self._FunctionList.append(self._Meteors_Bouncy_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Bouncy_Function(self):
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
						# print('[{}] = meteor[{}]'.format(meteor.index, index))
						meteor.previousIndex = newLocation
						meteor.bounce = False
						if self._Explode:
							middle = meteor.moveRange[len(meteor.moveRange)//2]
							explosions.append(((middle-6) % self._VirtualLEDCount, Pixel(PixelColors.GRAY).Array))
							explosions.append(((middle-5) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).Array))
							explosions.append(((middle-4) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).Array))
							explosions.append(((middle-3) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).Array))
							explosions.append(((middle-2) % self._VirtualLEDCount, Pixel(PixelColors.RED).Array))
							explosions.append(((middle-1) % self._VirtualLEDCount, Pixel(PixelColors.RED).Array))
							explosions.append(((middle+1) % self._VirtualLEDCount, Pixel(PixelColors.RED).Array))
							explosions.append(((middle+2) % self._VirtualLEDCount, Pixel(PixelColors.RED).Array))
							explosions.append(((middle+3) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).Array))
							explosions.append(((middle+4) % self._VirtualLEDCount, Pixel(PixelColors.ORANGE).Array))
							explosions.append(((middle+5) % self._VirtualLEDCount, Pixel(PixelColors.YELLOW).Array))
							explosions.append(((middle+6) % self._VirtualLEDCount, Pixel(PixelColors.GRAY).Array))
			for index, meteor in enumerate(self._LightDataObjects):
				try:
					if meteor.index > self._VirtualLEDCount:
						meteor.index = meteor.index % (self._VirtualLEDCount -1)
					self._VirtualLEDArray[meteor.index] = meteor.colors[meteor.colorindex]
				except:
					# print('len(self._LightDataObjects)={},len(meteor[{}]={}, itms[{},{}] len(LEDS)={}'.format(len(self._LightDataObjects), led, len(self._LightDataObjects[led]), index, color, len(self._VirtualLEDArray)))
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


	def Do_Meteors_Again(self, refreshDelay=0.001, colorSequence=[PixelColors.RED,PixelColors.WHITE, PixelColors.GREEN], backgroundColor=PixelColors.OFF, maxDelay=5, fadeSteps=25, randomColors=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			fadeAmount = 255//fadeSteps
			while (fadeAmount * fadeSteps) < 256:
				fadeAmount += 1
			self._Meteors_Again_Configuration(colorSequence=colorSequence, maxDelay=maxDelay, fadeAmount=fadeAmount, fadeSteps=fadeSteps)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Again_Configuration(self, colorSequence, maxDelay, fadeAmount, fadeSteps):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
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
			self._FunctionList.append(self._Meteors_Again_Function)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Meteors_Again_Function(self):
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


	def Do_Paint(self, refreshDelay=0.001, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE,PixelColors.OFF], backgroundColor=PixelColors.OFF, maxDelay=10, randomColors=False):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=self.BackgroundColor))
			self._Paint_Configuration(randomColors=randomColors, colorSequence=colorSequence, maxDelay=maxDelay)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Paint_Configuration(self, randomColors, colorSequence, maxDelay):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._RandomColors = randomColors
			self.ColorSequence = colorSequence
			self._MaxDelay = maxDelay
			for index, color in enumerate(self.ColorSequence):
				paintBrush = LightData(color)
				paintBrush.index = random.randint(0, self._VirtualLEDCount-1)
				paintBrush.step = (-1, 1)[random.randint(0,1)]
				paintBrush.delayCountMax = random.randint(10, self._MaxDelay)
				paintBrush.stepCountMax = random.randint(2, self._VirtualLEDCount*2)
				paintBrush.colorSequenceIndex = index
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
						# if self._RandomColors:
							# paintBrush[color] = COLORS_NO_OFF[list(COLORS_NO_OFF.keys())[random.randint(0,len(COLORS_NO_OFF.keys())-1)]]
				self._VirtualLEDArray[paintBrush.index] = paintBrush.colors[paintBrush.colorindex]
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Sprites(self, refreshDelay=0.03, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.WHITE], backgroundColor=PixelColors.OFF, fadeAmount=3, randomColors=True):
		"""
		"""
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=self.BackgroundColor))
			self._Sprites_Configuration(fadeAmount=fadeAmount, colorSequence=colorSequence, randomColors=randomColors)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Sprites_Configuration(self, fadeAmount, colorSequence, randomColors):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeAmount = fadeAmount
			self.ColorSequence = colorSequence
			for index, color in enumerate(self.ColorSequence):
				sprite = LightData(color)
				sprite.active = False
				sprite.index = random.randint(0, self._VirtualLEDCount-1)
				sprite.lastindex = sprite.index
				sprite.direction = [-1,1][random.randint(0,1)]
				sprite.colorSequenceIndex = index
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
			for ledIndex in range(len(self._VirtualLEDArray)):
				self._FadeLED(ledIndex, self.BackgroundColor, self._FadeAmount)
			for sprite in self._LightDataObjects:
				if sprite.active:
					still_alive = random.randint(6,40) > sprite.duration
					if still_alive:
						sprite.lastindex = sprite.index
						step_size = random.randint(1,3)*sprite.direction
						#print(step_size
						#sprite[sprite_direction] = step_size * 2
						mi = min(sprite.index, sprite.index + step_size)
						ma = max(sprite.index, sprite.index + step_size)
						#print(mi, ma
						first = True
						if sprite.direction > 0:
							for index in range(mi+1, ma+1):
								index = index % self._VirtualLEDCount
								#print('setting index',index,self._VirtualLEDArray[sprite[sprite_index]]
								sprite.index = index
								self._VirtualLEDArray[sprite.index] = sprite.colors[sprite.colorindex]
								if not first:
									self._FadeLED(index, self.BackgroundColor, self._FadeAmount)
								first - False
							#sprite[sprite_index] = ma
						else:
							for index in range(ma-1, mi-1,-1):
								index = index % self._VirtualLEDCount
								#print('setting index',index
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
						# if True == self._RandomColors:
							# sprite.colors[sprite.colorindex] = COLORS_NO_OFF[list(COLORS_NO_OFF.keys())[random.randint(0,len(COLORS_NO_OFF.keys())-1)]]
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
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=LightPattern.SolidColorArray(arrayLength=self._WS281xLightCount, color=backgroundColor))
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._TwinkleChance = float(twinkleChance)
			self._TwinkleColorList = LightPattern._FixColorSequence(twinkleColors)
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
					for LEDIndex in range(self._WS281xLightCount):
						doLight = random.randint(0,maxVal)
						if doLight > maxVal * (1.0 - self._TwinkleChance):
							self._WS281xLights[LEDIndex] = color
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
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=PixelColors.OFF, ledArray=LightPattern.ColorTransitionArray(arrayLength=self._WS281xLightCount, colorSequence=colorSequence))
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
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._BlinkChance = float(blinkChance)
			self._BlinkColorList = LightPattern._FixColorSequence(blinkColors)
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
						for LEDIndex in range(self._WS281xLightCount):
							self._WS281xLights[LEDIndex] = color
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def Do_Raindrops(self, refreshDelay=0.001, colorSequence=[PixelColors.RED, PixelColors.GREEN, PixelColors.WHITE], maxSize=15, backgroundColor=PixelColors.OFF, fadeAmount=25):
		try:
			LOGGER.debug('\n%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._Initialize(refreshDelay=refreshDelay, backgroundColor=backgroundColor, ledArray=None)
			self._Raindrops_Configuration(colorSequence, fadeAmount=fadeAmount, maxSize=maxSize)
			self._Run()
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise

	def _Raindrops_Configuration(self, colorSequence, fadeAmount, maxSize):
		try:
			LOGGER.debug('%s.%s:', self.__class__.__name__, inspect.stack()[0][3])
			self._FadeAmount = fadeAmount
			self.ColorSequence = colorSequence
			for index, color in enumerate(self.ColorSequence):
				raindrop = LightData(color)
				raindrop.maxSize = maxSize
				raindrop.index = random.randint(0, self._VirtualLEDCount-1)
				raindrop.stepCountMax = random.randint(2, raindrop.maxSize//2)
				raindrop.fadeAmount = 192 // raindrop.stepCountMax
				raindrop.active = False
				raindrop.activeChance = 0.2
				raindrop.colorSequenceIndex = index
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
						raindrop.colors[raindrop.colorindex] = self.ColorSequence[raindrop.colorSequenceIndex]
						raindrop.active = False
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('%s.%s Exception: %s', self.__class__.__name__, inspect.stack()[0][3], ex)
			raise


	def demo(self, secondsPerMode=20):
		self.SecondsPerMode = secondsPerMode
		for func in dir(self):
			if func.lower()[:3] == 'do_':
				getattr(self, func)()


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

		if hasattr(colors, '__len__') and hasattr(colors, 'shape') and len(colors.shape)>1:
			self.colors = LightPattern._FixColorSequence(colors)
		else:
			self.colors = [np.array(Pixel(colors).Tuple)]
		self.colorindex = 0

if __name__ == '__main__':
	try:
		func = LightFunction(debug=True)
		func.SecondsPerMode=0.2

		func.Do_SolidColor()
		func.Do_SolidColor_Random()
		func.Do_SolidColor_Cycle_Sequence()
		func.Do_SolidColor_Cycle_Rainbow()

		func.Do_Shift_Sequence()
		func.Do_Shift_SequenceRepeating()
		func.Do_Shift_Rainbow()
		func.Do_Shift_Emily1()
		func.Do_Shift_Lily1()

		func.Do_Shift_Fade_Sequence()

		func.Do_Alternate_Sequence()
		func.Do_Alternate_Rainbow()
		func.Do_Alternate_CylonEye()

		func.Do_BetterCylon()

		func.Do_Merge_Sequence()
		func.Do_Merge_Rainbow()
		func.Do_Merge_Wintergreen()

		func.Do_Accelerate_Sequence()
		func.Do_Accelerate_Rainbow()
		func.Do_Accelerate_Wes1()

		func.Do_Random_Change()
		func.Do_Random_Change_Fade()

		func.Do_Meteors()
		func.Do_Meteors_Fancy()
		func.Do_Meteors_Bouncy()
		func.Do_Meteors_Again()

		func.Do_Paint()

		func.Do_Sprites()

		func.Do_Twinkle()
		func.Do_Peppermint()
		func.Do_Girly()
		func.Do_Spaz()

		func.Do_Raindrops()

	except KeyboardInterrupt:
		pass
	except SystemExit:
		pass