#!/usr/bin/python3
"""An example of using this module."""
import LightBerries.LightPatterns
from LightBerries.LightControl import LightController
from LightBerries.LightPixels import PixelColors

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
# to understand the rest of these arguments read
# their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0


# create the LightBerries Controller object
lightControl = LightController(
    ledCount=PIXEL_COUNT,
    pwmGPIOpin=GPIO_PWM_PIN,
    channelDMA=DMA_CHANNEL,
    frequencyPWM=PWM_FREQUENCY,
    channelPWM=PWM_CHANNEL,
    invertSignalPWM=INVERT,
    gamma=GAMMA,
    stripTypeLED=LED_STRIP_TYPE,
    ledBrightnessFloat=BRIGHTNESS,
    debug=True,
)
# configure a color pattern using a "useColor" method
lightControl.useColorSequence(
    colorSequence=LightBerries.LightPatterns.DefaultColorSequence(),
    backgroundColor=PixelColors.OFF,
)
# configure a function using a "useFunction" method
lightControl.useFunctionRaindrops(
    maxSize=12,
    raindropChance=0.05,
    stepSize=1,
    maxRaindrops=3,
    fadeAmount=0.4,
)
# run the configuration until killed
try:
    lightControl.run()
except KeyboardInterrupt:
    pass
except SystemExit:
    pass
# turn all LEDs off
lightControl.off()
# cleanup memory
del lightControl
