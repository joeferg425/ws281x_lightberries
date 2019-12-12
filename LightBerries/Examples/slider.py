import tkinter as tk
from LightBerries import LightFunction, Pixel
from tkinter.colorchooser import *

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
		self.slider = tk.Scale(self.root, from_=0, to=0xFFFFFF, orient="horizontal", command=self.updateValue)
		self.slider.pack()
		self.button = tk.Button(text='Select Color', command=self.getColor)
		self.button.pack()
		self.lightFunction = LightFunction(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
		self.root.title('Color Chooser')
		self.root.mainloop()


	def getColor(self):
		color = askcolor()
		color = int(color[1][1:],16)
		self.lightFunction._VirtualLEDArray[:] *=0
		self.lightFunction._VirtualLEDArray[:] += Pixel(color).array
		self.lightFunction._CopyVirtualLedsToWS281X()
		self.lightFunction._RefreshLEDs()

	def updateValue(self, color):
		color = int(color)
		self.lightFunction._VirtualLEDArray[:] *=0
		self.lightFunction._VirtualLEDArray[:] += Pixel(color).array
		self.lightFunction._CopyVirtualLedsToWS281X()
		self.lightFunction._RefreshLEDs()

app = App()