#!/usr/bin/python3
from lightberries import MatrixController
from PIL import Image
import numpy as np
import time

# import cv2

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
BRIGHTNESS = 0.15
BRIGHTNESS = 1.0
# to understand the rest of these arguments read
# their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0


# create the lightberries Controller object
lightControl = MatrixController(
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

img = Image.open("image.bmp")
img.load()
data = np.asarray(img, dtype="int32")
temp = data[:, :, 0].copy()
data[:, :, 0] = data[:, :, 1]
data[:, :, 1] = temp
data[:] = data.astype(np.float32) * 0.5
lightControl.setvirtualLEDBuffer(data)
lightControl.copyVirtualLedsToWS281X()
lightControl.refreshLEDs()
time.sleep(10)
input('hit enter to exit')
lightControl.off()