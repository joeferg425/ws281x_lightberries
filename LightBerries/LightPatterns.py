import numpy as np
import random
import logging
from typing import List, Tuple
from .Pixels import Pixel, PixelColors
from .WS281XLights import LightString


LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
	streamHandler = logging.StreamHandler()
	LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)

class LightPattern:
	@staticmethod
	def _PixelArray(arrayLength:int) -> List[List[int]]:
		"""
		Creates array of RGB tuples that are all one color
		"""
		try:
			arrayLength = int(arrayLength)
			return np.array([np.array(PixelColors.OFF.value.Tuple) for i in range(arrayLength)])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}._PixelArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def _FixColorSequence(colorSequence:List[any]) -> List[Pixel]:
		try:
			return np.array([Pixel(p).Tuple for p in colorSequence])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}._FixColorSequence: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def SolidColorArray(arrayLength:int, color:Pixel=PixelColors.WHITE) -> List[List[int]]:
		"""
		Creates array of RGB tuples that are all one color
		"""
		try:
			arrayLength = int(arrayLength)
			if not isinstance(color, Pixel):
				color = Pixel(color)
			return np.array([color.Tuple for i in range(arrayLength)])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.SolidColorArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def WesArray() -> List[List[int]]:
		"""
		creates Wes's color buffer to be shifted in
		"""
		try:
			return LightPattern._FixColorSequence([PixelColors.WHITE, PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.RED, PixelColors.BLUE, PixelColors.GREEN])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.WesArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def ColorTransitionArray(arrayLength:int, colorSequence:List[Pixel]=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE,PixelColors.WHITE]) -> List[List[int]]:
		"""
		This is a slightly more versatile version of CreateRainbow.
		The user specifies a color sequence and the number of steps (LEDS)
		in the transition from one color to the next.

		arrayLength: int
			The total totalArrayLength of the final sequence in LEDs
			This parameter is optional and defaults to LED_INDEX_COUNT

		colorSequence: array(tuple(int,int,int))
			a sequence of colors to merge between

		stepCount: int
			The number of LEDs it takes to transition between one color and the next.
			This parameter is optional and defaults to 'totalArrayLength / len(sequence)'.
		"""
		try:
			# get length of sequence
			colorSequence = LightPattern._FixColorSequence(colorSequence)
			sequenceLength = len(colorSequence)
			derive=False
			count = 0
			stepCount = None
			# figure out how many LED's per color change
			if stepCount is None:
				derive = True
				stepCount = arrayLength // sequenceLength
				prevStepCount = stepCount
			# create temporary array
			arry = LightPattern._PixelArray(arrayLength)
			# step through color sequence
			for colorIndex in range(sequenceLength):
				if colorIndex == sequenceLength - 1 and derive==True:
					stepCount = arrayLength - count
				# figure out the current and next colors
				thisColor = colorSequence[colorIndex]
				nextColor = colorSequence[(colorIndex + 1) % sequenceLength]
				# handle red, green, and blue individually
				for rgbIndex in range(len(thisColor)):
					i = colorIndex * prevStepCount
					# linspace creates the array of values from arg1, to arg2, in exactly arg3 steps
					arry[i:i+stepCount,rgbIndex] = np.linspace(thisColor[rgbIndex],nextColor[rgbIndex],stepCount)
				count += stepCount
			return arry.astype(int)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.ColorTransitionArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def RainbowArray(arrayLength:int) -> List[List[int]]:
		"""
		create a color gradient array

		arrayLength: int
			The length of the gradient array to create.
			(the number of LEDs in the rainbow)
		"""
		try:
			return LightPattern.ColorTransitionArray(arrayLength=arrayLength, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.RainbowArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def RepeatingColorSequenceArray(arrayLength:int, colorSequence:List[Pixel]=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE]) -> List[List[int]]:
		"""
		Creates a repeating LightPattern from a given sequence

		Parameters:
			arrayLength: int
				The length of the gradient array to create.
				(the number of LEDs in the rainbow)

			colorSequence: array(tuple(int,int,int))
				sequence of RGB tuples

		"""
		try:
			arrayLength = int(arrayLength)
			colorSequence = LightPattern._FixColorSequence(colorSequence)
			sequenceLength = len(colorSequence)
			arry = LightPattern._PixelArray(arrayLength=arrayLength)
			arry[0:sequenceLength] = colorSequence
			for i in range(0, arrayLength, sequenceLength):
				if i + sequenceLength <= arrayLength:
					arry[i:i+sequenceLength] = arry[0:sequenceLength]
				else:
					extra = (i + sequenceLength) % arrayLength
					end = (i + sequenceLength) - extra
					arry[i:end] = arry[0:(sequenceLength-extra)]
			return arry
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.RepeatingColorSequenceArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def RepeatingRainbowArray(arrayLength:int, segmentLength:int=None) -> List[List[int]]:
		"""
		Creates a repeating gradient for you

		Parameters:
			arrayLength: int
				the number of LEDs to involve in the rainbow

			colorSkip: RED, GREEN, or BLUE
				RGB color tuple
		"""
		if segmentLength is None:
			segmentLength = arrayLength // 4
		try:
			return LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength))
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.RepeatingRainbowArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def ReflectArray(arrayLength:int, colorSequence:List[Pixel]=[PixelColors.RED, PixelColors.RED, PixelColors.GREEN, PixelColors.GREEN, PixelColors.BLUE, PixelColors.BLUE]) -> List[List[int]]:
		"""
		generates an array where each repetition of the input
		sequence is reversed from the previous

		Parameters:
			totalArrayLength: int
				the number of LEDs to involve in the rainbow

			sequence: array(tuple(int,int,int))
				an array of RGB tuples
		"""
		# if user didn't specify otherwise, fold in middle
		try:
			arrayLength = int(arrayLength)
			colorSequence = LightPattern._FixColorSequence(colorSequence)
			foldLength = len(colorSequence)
			flip = False
			arry = LightPattern._PixelArray(arrayLength)
			for segBegin in range(0, arrayLength, foldLength):
				overflow = 0
				if segBegin + foldLength <= arrayLength:
					segEnd = segBegin + foldLength
				else:
					overflow = ((segBegin + foldLength) % arrayLength)
					segEnd = (segBegin + foldLength) - overflow
				if flip:
					arry[segBegin:segEnd] = colorSequence[foldLength-overflow-1::-1]
				else:
					arry[segBegin:segEnd] = colorSequence[0:foldLength-overflow]
				flip = not flip
			return arry
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.ReflectArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def TrueRandomArray(arrayLength=None):
		"""
		Creates an array of random colors

		Parameters:
			count: int
				the number of random colors to generate for the array
		"""
		try:
			arry = LightPattern._PixelArray(arrayLength)
			for i in range(arrayLength):
				# prevent 255, 255, 255
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
				arry[i] = [redLED, greenLED, blueLED]
			return arry
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.RandomArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def ColorStretchArray(repeats = 5, colorSequence:List[Pixel]=[PixelColors.RED, PixelColors.ORANGE2, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.BLUE, PixelColors.PURPLE]):
		"""
		"""
		try:
			colorSequence = LightPattern._FixColorSequence(colorSequence)
			colorSequenceLength = len(colorSequence)
			# repeats = arrayLength // colorSequenceLength
			arry = LightPattern._PixelArray(colorSequenceLength * repeats)
			for i in range(colorSequenceLength):
				arry[i*repeats:(i+1)*repeats] = colorSequence[i]
			return arry
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.RandomArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def Emily1():
		"""
		"""
		try:
			return LightPattern._FixColorSequence([PixelColors.RED, PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.PURPLE, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.PURPLE, PixelColors.BLUE])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.error('Error in {}.RandomArray: {}'.format('LightPatterns', ex))
			raise

if __name__ == '__main__':
	import time
	lights = LightString()
	lightLength = len(lights)
	delay = 2

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.SolidColorArray(lightLength, PixelColors.WHITE)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.WesArray()
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.ColorTransitionArray(lightLength)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.RainbowArray(lightLength)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.RepeatingColorSequenceArray(lightLength)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.RepeatingRainbowArray(lightLength)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.ReflectArray(lightLength)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	# p = LightPattern._PixelArray(lightLength)
	# lights[:len(p)] = p
	# p = LightPattern.RandomArray(lightLength)
	# lights[:len(p)] = p
	# lights.Refresh()
	# time.sleep(delay)

	p = LightPattern._PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.ColorStretchArray(lightLength)
	lights[:len(p)] = p
	lights.Refresh()
	time.sleep(delay)
