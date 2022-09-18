#!/usr/bin/python3
from lightberries import MatrixController
from PIL import Image
import numpy as np
import sys

# the number of pixels in the light string
PIXEL_ROW_COUNT = 16
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
MATRIX_LAYOUT = np.array(
    [
        [1, 2],
        [0, 3],
    ]
)
MATRIX_SHAPE = (PIXEL_ROW_COUNT, PIXEL_COLUMN_COUNT)

# create the lightberries Controller object
lightControl = MatrixController(
    ledXaxisRange=PIXEL_ROW_COUNT * 2,
    ledYaxisRange=PIXEL_COLUMN_COUNT * 2,
    pwmGPIOpin=GPIO_PWM_PIN,
    channelDMA=DMA_CHANNEL,
    frequencyPWM=PWM_FREQUENCY,
    channelPWM=PWM_CHANNEL,
    invertSignalPWM=INVERT,
    gamma=GAMMA,
    stripTypeLED=LED_STRIP_TYPE,
    ledBrightnessFloat=BRIGHTNESS,
    debug=True,
    matrixLayout=MATRIX_LAYOUT,
    matrixShape=MATRIX_SHAPE,
)

img = Image.open(sys.argv[1])
img.load()
data = np.asarray(img, dtype="int32")
temp = data[:, :, 0].copy()
data[:, :, 0] = data[:, :, 1]
data[:, :, 1] = temp
# data[:] = data.astype(np.float32) * 0.5
data[:, :, 0] = data[:, :, 0] * 0.9
data[:, :, 2] = data[:, :, 2] * 0.8
# data[:, :, :] = data * 0.6
data = np.rot90(data)
light_data = np.zeros((32, 32, 3), dtype=np.int32)
light_data[: data.shape[0], : data.shape[1]] = data
lightControl.virtualLEDBuffer = light_data
lightControl.copyVirtualLedsToWS281X()
lightControl.refreshLEDs()
input("hit enter to exit")
lightControl.off()
