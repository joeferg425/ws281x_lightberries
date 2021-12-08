# WS281X_LightBerries #

## About ##

Wrapper for rpi_ws281x [github.com/rpi-ws281x/rpi-ws281x-python](https://github.com/rpi-ws281x/rpi-ws281x-python) library that defines a bunch of colorful functions.

This library has only been tested on raspberry pi 2 and raspberry pi 3. The lights I have are ws2811 50ct off of amazon with a custom 5v power supply and level converter.

This library is intended for a string of lights not a matrix configuration.

## Installation #

```sh
# from command line run:
sudo pip3 install lightberries

# alternately use pip if python3 is the only python on your system
sudo pip install lightberries
```

## Examples ##

### Quick Demo ###

```sh
# run an endless random demo of functions and light-patterns that assumes you have 100 LEDs
# press CTRL+C to exit the demo

#### Makes the following assumptions ###
## # the number of pixels in the light string
## PIXEL_COUNT = 100
## # GPIO pin to use for PWM signal
## GPIO_PWM_PIN = 18
## # DMA channel
## DMA_CHANNEL = 5
## # frequency to run the PWM signal at
## PWM_FREQUENCY = 800000
## RGB addressing versus GRB
## DEFAULT_PIXEL_ORDER = LED_ORDER.GRB

sudo python3 -m LightBerries
```

### Full Demo ###

```python
# import the library
from LightBerries import LightController
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
lightController = LightController(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
# choose a function
lightController.demo(secondsPerMode=5)
```

### Rainbow that scrolls across the lights ###

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
lightController = LightController(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
# choose a function
lightController.useColorRainbow()
lightController.functionMarquee()
lightController.run()
```

### Raindrop function ###

```python
# import the library
from LightBerries import LightController
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
lightController = LightController(ledCount=PIXEL_COUNT, pwmGPIOpin=GPIO_PWM_PIN, channelDMA=DMA_CHANNEL, frequencyPWM=PWM_FREQUENCY, channelPWM=PWM_CHANNEL, invertSignalPWM=INVERT, gamma=GAMMA, stripTypeLED=LED_STRIP_TYPE, ledBrightnessFloat=BRIGHTNESS, debug=True)
# choose a function
lightController.useColorRandom()
lightController.functionRaindrops()
lightController.run()
```
