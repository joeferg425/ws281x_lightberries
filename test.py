from LightBerries import LightFunction, PixelColors

# the number of pixels in the light string
PIXEL_COUNT = 100
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
# create the light-function object
lightFunction = LightFunction(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
try:
	function_names=[]
	color_names=[]
	function_names=['bouncy']
	skip_functions=['accelerate', 'alternate', 'cylon', 'merge', 'randomchange', 'shift', 'shiftfade', 'solidcolor', 'solidcolorcycle', 'randomchangefade']
	skip_colors=[]
	# color_names=['rainbow']
	secondsPerMode=10
	lightFunction.test(secondsPerMode=secondsPerMode, function_names=function_names, color_names=color_names, skip_functions=skip_functions, skip_colors=skip_colors)
	# lightFunction.demo()
	# lightFunction.functionAlternate()
	# lightFunction.functionSolidColorCycle()
	# lightFunction.pattern_SingleColor()
	# lightFunction.pattern_SinglePseudoRandomColor()
	# lightFunction.useColorSequence()
	# lightFunction.color_SequenceRepeating()
	# lightFunction.pattern_ColorTransition()
	# lightFunction.color_TransitionRepeating()
	# lightFunction.color_Rainbow()
	# lightFunction.color_RainbowRepeating()
	# lightFunction.run()
except KeyboardInterrupt:
	pass
except SystemExit:
	pass
except Exception:
	raise
