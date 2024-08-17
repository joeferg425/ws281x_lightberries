#!/usr/bin/python3
"""An example of using this module."""
from lightberries.array_controller import ArrayController

# the number of pixels in the light string
PIXEL_COUNT = 256
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
lightControl = ArrayController(
    led_count=PIXEL_COUNT,
    pwm_gpio_pin=GPIO_PWM_PIN,
    dma_channel=DMA_CHANNEL,
    pwm_frequency=PWM_FREQUENCY,
    pwm_channel=PWM_CHANNEL,
    pwm_invert_signal=INVERT,
    gamma=GAMMA,
    led_strip_type=LED_STRIP_TYPE,
    led_brightness=BRIGHTNESS,
    debug=True,
)
# run the configuration until killed
try:
    lightControl.demo(seconds_per_mode=30, skip_functions=["none", "solid"], skip_colors=["single"])
except KeyboardInterrupt:
    pass
except SystemExit:
    pass
# turn all LEDs off
lightControl.off()
# cleanup memory
del lightControl
