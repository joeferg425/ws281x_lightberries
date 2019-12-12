import numpy as np
import random
import logging
from typing import List, Tuple
from .Pixels import Pixel, PixelColors
from .LightStrings import LightString


LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
	streamHandler = logging.StreamHandler()
	LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)

class LightPattern:
	""" This class defines several functions for easily creating static color patterns """
	@staticmethod
	def PixelArray(arrayLength:int) -> List[Pixel]:
		""" Creates array of RGB tuples that are all off

		arrayLength: int
			the number of pixels desired in the returned pixel array

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			arrayLength = int(arrayLength)
			return np.array([PixelColors.OFF.array for i in range(arrayLength)])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.PixelArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def ConvertPixelArrayToNumpyArray(colorSequence:List[any]) -> np.ndarray:
		""" Convert an array of Pixels into a numpy array of rgb arrays

		colorSequence: List[Pixel]
			a list of Pixel objects

		returns: List[Pixel]
			a numpy array of int arrays representing a string of rgb values
		"""
		try:
			return np.array([Pixel(p).tuple for p in colorSequence])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.ConvertPixelArrayToNumpyArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def SolidColorArray(arrayLength:int, color:Pixel=PixelColors.WHITE) -> List[Pixel]:
		""" Creates array of RGB tuples that are all one color

		arrayLength: int
			the total desired length of the return array

		color: Pixel
			a pixel object defining the rgb values you want in the pattern

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			arrayLength = int(arrayLength)
			if not isinstance(color, Pixel):
				color = Pixel(color)
			return np.array([color.array for i in range(arrayLength)])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.SolidColorArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def WesArray() -> List[Pixel]:
		"""	creates a color array that Wes wanted

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			return LightPattern.ConvertPixelArrayToNumpyArray([PixelColors.WHITE, PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.RED, PixelColors.BLUE, PixelColors.GREEN])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.WesArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def ColorTransitionArray(arrayLength:int, wrap=True, colorSequence:List[Pixel]=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE,PixelColors.WHITE]) -> List[Pixel]:
		"""
		This is a slightly more versatile version of CreateRainbow.
		The user specifies a color sequence and the number of steps (LEDs)
		in the transition from one color to the next.

		arrayLength: int
			The total totalArrayLength of the final sequence in LEDs
			This parameter is optional and defaults to LED_INDEX_COUNT

		wrap: bool
			set true to wrap the transition from the last color back to the first

		colorSequence: array(tuple(int,int,int))
			a sequence of colors to merge between

		stepCount: int
			The number of LEDs it takes to transition between one color and the next.
			This parameter is optional and defaults to 'totalArrayLength / len(sequence)'.

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			# get length of sequence
			sequenceLength = len(colorSequence)
			# derive=False
			count = 0
			stepCount = None
			if wrap:
				wrap = 0
			else:
				wrap = 1
			# figure out how many LEDs per color change
			if stepCount is None:
				# derive = True
				stepCount = arrayLength // (sequenceLength - wrap)
				prevStepCount = stepCount
			# create temporary array
			arry = LightPattern.PixelArray(arrayLength)
			# step through color sequence
			for colorIndex in range(sequenceLength - wrap):
				if colorIndex == sequenceLength-1:
					stepCount = arrayLength - count
				elif colorIndex == sequenceLength-2:
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
			LOGGER.exception('Error in {}.ColorTransitionArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def RainbowArray(arrayLength:int, wrap:bool=False) -> List[Pixel]:
		""" create a color gradient array

		arrayLength: int
			The length of the gradient array to create.
			(the number of LEDs in the rainbow)

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			return LightPattern.ColorTransitionArray(arrayLength=arrayLength, colorSequence=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE,PixelColors.VIOLET], wrap=wrap)
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.RainbowArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def RepeatingColorSequenceArray(arrayLength:int, colorSequence:List[Pixel]=[PixelColors.RED,PixelColors.GREEN,PixelColors.BLUE]) -> List[Pixel]:
		"""
		Creates a repeating LightPattern from a given sequence

		arrayLength: int
			The length of the gradient array to create.
			(the number of LEDs in the rainbow)

		colorSequence: List[Pixel]
			sequence of RGB tuples

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			arrayLength = int(arrayLength)
			colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			sequenceLength = len(colorSequence)
			arry = LightPattern.PixelArray(arrayLength=arrayLength)
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
			LOGGER.exception('Error in {}.RepeatingColorSequenceArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def RepeatingRainbowArray(arrayLength:int, segmentLength:int=None) -> List[Pixel]:
		"""
		Creates a repeating gradient for you

		arrayLength: int
			the number of LEDs to involve in the rainbow

		segmentLength: int
			the length of each mini rainbow in the repeating sequence

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		if segmentLength is None:
			segmentLength = arrayLength // 4
		try:
			return LightPattern.RepeatingColorSequenceArray(arrayLength=arrayLength, colorSequence=LightPattern.RainbowArray(arrayLength=segmentLength, wrap=True))
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.RepeatingRainbowArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def ReflectArray(arrayLength:int, colorSequence:List[Pixel]=[PixelColors.RED, PixelColors.RED, PixelColors.GREEN, PixelColors.GREEN, PixelColors.BLUE, PixelColors.BLUE], foldLength=None) -> List[Pixel]:
		"""
		generates an array where each repetition of the input
		sequence is reversed from the previous

		arrayLength: int
			the number of LEDs to involve in the rainbow

		colorSequence: array(tuple(int,int,int))
			an array of RGB tuples

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		# if user didn't specify otherwise, fold in middle
		try:
			arrayLength = int(arrayLength)
			colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			colorSequenceLen = len(colorSequence)
			if foldLength is None:
				foldLength = arrayLength // 2
			if foldLength > colorSequenceLen:
				temp = LightPattern.PixelArray(foldLength)
				temp[foldLength - colorSequenceLen:] = colorSequence
				colorSequence = temp
				colorSequenceLen = len(colorSequence)
			flip = False
			arry = LightPattern.PixelArray(arrayLength)
			for segBegin in range(0, arrayLength, foldLength):
				overflow = 0
				if segBegin + foldLength <= arrayLength and segBegin + foldLength <= colorSequenceLen:
					segEnd = segBegin + foldLength
				elif segBegin + foldLength > arrayLength:
					segEnd = segBegin + foldLength
					overflow = ((segBegin + foldLength) % arrayLength)
					segEnd = (segBegin + foldLength) - overflow
				elif segBegin + foldLength > colorSequenceLen:
					segEnd = segBegin + colorSequenceLen
					overflow = ((segBegin + colorSequenceLen) % colorSequenceLen)
					segEnd = (segBegin + colorSequenceLen) - overflow

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
			LOGGER.exception('Error in {}.ReflectArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def RandomArray(arrayLength=None) -> List[Pixel]:
		"""
		Creates an array of random colors

		arrayLength: int
			the number of random colors to generate for the array

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			arry = LightPattern.PixelArray(arrayLength)
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
			LOGGER.exception('Error in {}.PseudoRandomArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def PseudoRandomArray(arrayLength=None, colorSequence=None) -> List[Pixel]:
		"""
		Creates an array of random colors

		arrayLength: int
			the number of random colors to generate for the array

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			arry = LightPattern.PixelArray(arrayLength)
			if not colorSequence is None:
				colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			for i in range(arrayLength):
				if colorSequence is None:
					arry[i] = PixelColors.pseudoRandom().array
				else:
					arry[i] = colorSequence[random.randint(0, len(colorSequence)-1)]
			return arry
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.PseudoRandomArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def ColorStretchArray(repeats = 5, colorSequence:List[Pixel]=[PixelColors.RED, PixelColors.ORANGE2, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.BLUE, PixelColors.PURPLE]) -> List[Pixel]:
		""" takes a sequence of input colors and repeats each element the requested number of times

		repeats: int
			the number of times to repeat each element oc colorSequence

		colorSequence: List[Pixel]
			a list of pixels defining the desired colors in the output array

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			colorSequence = LightPattern.ConvertPixelArrayToNumpyArray(colorSequence)
			colorSequenceLength = len(colorSequence)
			# repeats = arrayLength // colorSequenceLength
			arry = LightPattern.PixelArray(colorSequenceLength * repeats)
			for i in range(colorSequenceLength):
				arry[i*repeats:(i+1)*repeats] = colorSequence[i]
			return arry
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.PseudoRandomArray: {}'.format('LightPatterns', ex))
			raise

	@staticmethod
	def Emily1():
		"""
		defines a color pattern that emily requested

		returns: List[Pixel]
			a list of Pixel objects in the pattern you requested
		"""
		try:
			return LightPattern.ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.ORANGE, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.PURPLE, PixelColors.YELLOW, PixelColors.GREEN, PixelColors.PURPLE, PixelColors.BLUE])
		except SystemExit:
			raise
		except KeyboardInterrupt:
			raise
		except Exception as ex:
			LOGGER.exception('Error in {}.PseudoRandomArray: {}'.format('LightPatterns', ex))
			raise

if __name__ == '__main__':
	import time
	lights = LightString(gpioPin=18, ledDMA=5, ledCount=100, ledFrequency=800000)
	lightLength = len(lights)
	delay = 2

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.SolidColorArray(lightLength, PixelColors.WHITE)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.WesArray()
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.ColorTransitionArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.RainbowArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.RepeatingColorSequenceArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.RepeatingRainbowArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.ReflectArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.PseudoRandomArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)

	p = LightPattern.PixelArray(lightLength)
	lights[:len(p)] = p
	p = LightPattern.ColorStretchArray(lightLength)
	lights[:len(p)] = p
	lights.refresh()
	time.sleep(delay)
