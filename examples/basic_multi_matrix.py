#!/usr/bin/python3
"""An example of using this module."""
from lightberries.matrix_controller import MatrixController
import numpy as np

TEST = 1
TEST = 2
TEST = 4


# the number of pixels in the light string
if TEST == 1:
    PIXEL_ROW_COUNT = 16
else:
    PIXEL_ROW_COUNT = 32
if TEST == 4:
    PIXEL_COLUMN_COUNT = 32
else:
    PIXEL_COLUMN_COUNT = 16
# GPIO pin to use for PWM signal
GPIO_PWM_PIN = 18
# DMA channel
DMA_CHANNEL = 10
# frequency to run the PWM signal at
PWM_FREQUENCY = 800000
# brightness of LEDs in range [0.0, 1.0]
BRIGHTNESS = 0.1
# to understand the rest of these arguments read
# their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0
MATRIX_SHAPE = (16, 16)
if TEST == 1:
    MATRIX_LAYOUT = np.array(
        [
            [0],
        ],
    )
elif TEST == 2:
    MATRIX_LAYOUT = np.array(
        [
            [1],
            [0],
        ],
    )
else:
    MATRIX_LAYOUT = np.array(
        [
            [1, 2],
            [0, 3],
        ],
    )

# create the lightberries Controller object
lightControl = MatrixController(
    ledXaxisRange=PIXEL_COLUMN_COUNT,
    ledYaxisRange=PIXEL_ROW_COUNT,
    pwmGPIOpin=GPIO_PWM_PIN,
    channelDMA=DMA_CHANNEL,
    frequencyPWM=PWM_FREQUENCY,
    channelPWM=PWM_CHANNEL,
    invertSignalPWM=INVERT,
    gamma=GAMMA,
    stripTypeLED=LED_STRIP_TYPE,
    ledBrightnessFloat=BRIGHTNESS,
    debug=True,
    matrixShape=MATRIX_SHAPE,
    matrixLayout=MATRIX_LAYOUT,
)

# lightControl.useFunctionMatrixBounce(ballCount=6)
lightControl.useFunctionMatrixMarqueeText(text="this is a test of the broadcast system", delayCount=0)
try:
    lightControl.run()
except KeyboardInterrupt:
    pass
except SystemExit:
    pass
finally:
    # turn all LEDs off
    lightControl.off()
    # cleanup memory
    del lightControl
