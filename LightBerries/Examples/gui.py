import tkinter as tk
from LightBerries import LightFunction, Pixel, LightPattern
from tkinter.colorchooser import *
import time

# the number of pixels in the light string
PIXEL_COUNT = 196
# GPIO pin to use for PWM signal
GPIO_PWM_PIN = 18
# DMA channel
DMA_CHANNEL = 10
# frequency to run the PWM signal at
PWM_FREQUENCY = 800000
# brightness of LEDs in range [0.0, 1.0]
BRIGHTNESS = 0.75
# to understand the rest of these arguments read their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0

class App:
	def __init__(self):
		self.root = tk.Tk()
		self.lightFunction = None

		self.LEDCountInt = tk.IntVar()
		self.LEDCountInt.trace("w", lambda name, index, mode, var=self.LEDCountInt:self.updateLEDCount(var.get()))
		self.LEDCountlabel = tk.Label(text='LED Count')
		self.LEDCountlabel.grid(row=0, column=0)
		self.LEDCountslider = tk.Scale(self.root, from_=0, to=500, variable=self.LEDCountInt, orient="horizontal")
		self.LEDCountslider.grid(row=0, column=1)
		self.LEDCounttext = tk.Entry(self.root, textvariable=self.LEDCountInt)
		self.LEDCounttext.grid(row=0, column=2)
		self.LEDCountInt.set(PIXEL_COUNT)

		self.ColorInt = tk.IntVar()
		self.ColorString = tk.StringVar()
		self.ColorInt.trace("w", lambda name, index, mode, var=self.ColorInt:self.updateColor(var.get()))
		self.ColorString.trace("w", lambda name, index, mode, var=self.ColorString:self.updateColorHex(var.get()))
		self.Colorlabel = tk.Label(text='Color')
		self.Colorlabel.grid(row=1, column=0)
		self.Colorslider = tk.Scale(self.root, from_=0, to=0xFFFFFF, variable=self.ColorInt, orient="horizontal")
		self.Colorslider.grid(row=1, column=1)
		self.Colortext = tk.Entry(self.root, textvariable=self.ColorString)
		self.Colortext.grid(row=1, column=2)
		self.Colorbutton = tk.Button(text='Select Color', command=self.getColor)
		self.Colorbutton.grid(row=1, column=3)

		self.functionString = tk.StringVar()
		self.functionChoices = [f for f in dir(LightFunction) if f[:8] == 'function']
		self.functionChoices.sort()
		self.functionString.set(self.functionChoices[0])
		self.functionDropdown = tk.OptionMenu(self.root, self.functionString, *self.functionChoices)
		self.functionDropdown.grid(row=2, column=1)
		self.patternString = tk.StringVar()
		self.patternChoices = [f for f in dir(LightFunction) if f[:8] == 'useColor']
		self.patternChoices.sort()
		self.patternString.set(self.patternChoices[0])
		self.patternDropdown = tk.OptionMenu(self.root, self.patternString, *self.patternChoices)
		self.patternDropdown.grid(row=2, column=2)

		self.durationInt = tk.IntVar()
		self.durationInt.set(10)
		self.durationInt.trace("w", lambda name, index, mode, var=self.durationInt:self.updateDuration(var.get()))
		self.durationLabel = tk.Label(text='Duration (Seconds)')
		self.durationLabel.grid(row=3, column=1)
		self.durationText = tk.Entry(self.root, textvariable=self.durationInt)
		self.durationText.grid(row=3, column=2)
		self.buttonGo = tk.Button(self.root, height=1, width=10, text="Go", command=self.go)
		self.buttonGo.grid(row=3, column=3)


		self.lightFunction = LightFunction(ledCount=self.LEDCountInt.get(), pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
		self.root.title('Color Chooser')


		self.root.mainloop()

	def go(self):
		self.lightFunction.reset()
		getattr(self.lightFunction, self.patternString.get())()
		getattr(self.lightFunction, self.functionString.get())()
		self.lightFunction.secondsPerMode = self.durationInt.get()
		self.lightFunction.run()
		self.lightFunction._off()
		self.lightFunction._CopyVirtualLedsToWS281X()
		self.lightFunction._RefreshLEDs()
		time.sleep(0.01)

	def getColor(self):
		color = askcolor()
		color = int(color[1][1:],16)
		self.ColorInt.set(color)


	def updateDuration(self, duration):
		self.lightFunction.secondsPerMode = duration
		# self.lightFunction._VirtualLEDArray[:] *=0
		# self.lightFunction._VirtualLEDArray[:] += Pixel(color).array
		# self.lightFunction._CopyVirtualLedsToWS281X()
		# self.lightFunction._RefreshLEDs()

	# def updateLEDCountslider(self, color):
		# color = int(color)
		# self.lightFunction._VirtualLEDArray[:] *=0
		# self.lightFunction._VirtualLEDArray[:] += Pixel(color).array
		# self.lightFunction._CopyVirtualLedsToWS281X()
		# self.lightFunction._RefreshLEDs()
		# self.LEDCountString.set('{:06X}'.format(color))

	def updateLEDCount(self, count):
		# self.LEDCountInt.set(color)
		count = int(count)
		if not self.lightFunction is None:
			# print('count not null', self.lightFunction._VirtualLEDCount)
			self.lightFunction._VirtualLEDArray[:] *=0
			self.lightFunction._CopyVirtualLedsToWS281X()
			self.lightFunction._RefreshLEDs()
			time.sleep(0.01)
			self.lightFunction = LightFunction(ledCount=self.LEDCountInt.get(), pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
			# self.lightFunction._VirtualLEDArray[:] *=0
			self.lightFunction.secondsPerMode = self.durationInt.get()
			self.lightFunction._VirtualLEDArray[:] += Pixel(self.ColorInt.get()).array
			self.lightFunction._CopyVirtualLedsToWS281X()
			self.lightFunction._RefreshLEDs()
			time.sleep(0.01)

	def updateColor(self, color):
		if self.root.focus_get() != self.Colortext:
			self.ColorString.set('{:06X}'.format(color))
		if not self.lightFunction is None:
			# print('color not null', self.lightFunction._VirtualLEDCount)
			self.lightFunction._VirtualLEDArray[:] *=0
			self.lightFunction._VirtualLEDArray[:] += Pixel(color).array
			self.lightFunction._CopyVirtualLedsToWS281X()
			self.lightFunction._RefreshLEDs()
			time.sleep(0.01)

	def updateColorHex(self, color):
		color = int(color, 16)
		self.ColorInt.set(color)

app = App()