#!/usr/bin/python3
"""An example of using this module."""
import LightBerries.LightMatrixPatterns
from LightBerries.LightMatrixControls import LightMatrixController
from LightBerries.LightPixels import PixelColors

# the number of pixels in the light string
PIXEL_ROW_COUNT = 16
PIXEL_COLUMN_COUNT = 16
# PIXEL_ROW_COUNT = 3
# PIXEL_COLUMN_COUNT = 5
# GPIO pin to use for PWM signal
GPIO_PWM_PIN = 18
# DMA channel
DMA_CHANNEL = 10
# frequency to run the PWM signal at
PWM_FREQUENCY = 800000
# brightness of LEDs in range [0.0, 1.0]
BRIGHTNESS = 0.25
# to understand the rest of these arguments read
# their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0


# create the LightBerries Controller object
lightControl = LightMatrixController(
    ledRowCount=PIXEL_ROW_COUNT,
    ledColumnCount=PIXEL_COLUMN_COUNT,
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
# lightControl.useColorMatrix(
# matrix=LightBerries.LightMatrixPatterns.Spectrum2(PIXEL_ROW_COUNT * 10, PIXEL_COLUMN_COUNT),
# )
# lightControl.setVirtualLEDBuffer(
# LightBerries.LightMatrixPatterns.Spectrum2(PIXEL_ROW_COUNT, PIXEL_COLUMN_COUNT),
# )
# lightControl.setVirtualLEDBuffer(
# LightBerries.LightMatrixPatterns.SingleLED(PIXEL_ROW_COUNT, PIXEL_COLUMN_COUNT),
# )
lightControl.setVirtualLEDBuffer(
    LightBerries.LightMatrixPatterns.TextMatrix("hello world", color=PixelColors.pseudoRandom()),
)
# configure a function using a "useFunction" method
lightControl.useFunctionMatrixMarquee()
# lightControl.useFunctionMatrixColorFlux()
# lightControl.useColorSequencePseudoRandom()
# lightControl.useFunctionMatrixBounce(colorChange=True)
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