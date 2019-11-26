from numpy import array
from .Pixels import Pixel
from .LightPatterns import LightPattern

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
			self.colors = array([Pixel(colors).tuple])
