from numpy import array
from .Pixels import Pixel
from .LightPatterns import LightPattern

class LightData():
	def __init__(self, colors):
		self.index = 0
		self.lastindex = 0
		self.step = 0
		self.oldStep = 0
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
		self.colorIndex = 0
		self.random = False
		self.flipLength = 0
		if hasattr(colors, '__len__') and hasattr(colors, 'shape') and len(colors.shape)>1:
			self.color = None
			self.colors = LightPattern.ConvertPixelArrayToNumpyArray(colors)
		else:
			self.colors = array([Pixel(colors).tuple])
			self.color = Pixel(colors).array

	def __str__(self):
		return '[{}]: {}'.format(self.index, Pixel(self.colors[0]))

	def __repr__(self):
		return '<{}> {}'.format(self.__class__.__name__, str(self))
