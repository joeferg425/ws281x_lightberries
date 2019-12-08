# About:
Wrapper for rpi_ws281x (https://github.com/rpi-ws281x/rpi-ws281x-python) library that defines a bunch of colorful functions.

This library has only been tested on raspberry pi 2 and raspberry pi 3. The lights I have are ws2811 50ct off of amazon with a custom 5v power supply and level converter.

This library is intended for a string of lights not a matrix configuration.


# Installation:
	pip install lightberries-joeferg425


# Examples:

## Demo mode:
```python
# the number of pixels in the light string
PIXEL_COUNT = 100
# GPIO pin to use for PWM signal
GPIO_PWM_PIN = 18
# DMA channel
DMA_CHANNEL = 5
# frequency to run the PWM signal at
PWM_FREQUENCY = 800000
# brightness of LEDs in range [0.0, 1.0]
BRIGHTNESS = 0.5
# to understand the rest of these arguments read their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0
# create the light-function object
lightFunction = LightFunction(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
# choose a function
lightFunction.demo(secondsPerMode=5)
```
## Rainbow that scrolls across the lights:
```python
# the number of pixels in the light string
PIXEL_COUNT = 100
# GPIO pin to use for PWM signal
GPIO_PWM_PIN = 18
# DMA channel
DMA_CHANNEL = 5
# frequency to run the PWM signal at
PWM_FREQUENCY = 800000
# brightness of LEDs in range [0.0, 1.0]
BRIGHTNESS = 0.5
# to understand the rest of these arguments read their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0
# create the light-function object
lightFunction = LightFunction(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
# choose a function
lightFunction.useColorRainbow()
lightFunction.functionMarquee()
lightFunction.run()
```
## Raindrop function:
```python
# the number of pixels in the light string
PIXEL_COUNT = 100
# GPIO pin to use for PWM signal
GPIO_PWM_PIN = 18
# DMA channel
DMA_CHANNEL = 5
# frequency to run the PWM signal at
PWM_FREQUENCY = 800000
# brightness of LEDs in range [0.0, 1.0]
BRIGHTNESS = 0.5
# to understand the rest of these arguments read their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0
# create the light-function object
lightFunction = LightFunction(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
# choose a function
lightFunction.useColorRandom()
lightFunction.functionRaindrops()
lightFunction.run()
```
