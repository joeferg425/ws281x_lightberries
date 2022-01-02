"""Defines callable behaviors for this module."""
import argparse
import logging
import LightBerries
from LightBerries.LightControls import LightController

LOGGER = logging.getLogger("LightBerries")

if __name__ == "__main__":  # pylint: disable=invalid-name
    # the number of pixels in the light string
    PIXEL_COUNT = 100
    # GPIO pin to use for PWM signal
    GPIO_PWM_PIN = 18
    # DMA channel
    DMA_CHANNEL = 5
    # frequency to run the PWM signal at
    PWM_FREQUENCY = 800000
    # to understand the rest of these arguments read their
    # documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
    GAMMA = None
    LED_STRIP_TYPE = None
    INVERT = False
    PWM_CHANNEL = 0
    BRIGHTNESS = 0.75
    DURATION = 20.0
    FUNCTIONS = None
    COLORS = None

    # command-line args
    parser = argparse.ArgumentParser(
        description=LightBerries.__doc__, usage="sudo python3 -m LightBerries (Needs root for GPIO access)"
    )
    parser.add_argument("-l", "--LED_count", type=int, help="the number of LEDs in your LED string")
    parser.add_argument(
        "-d", "--function_duration", type=float, help="the duration of each random demo function in seconds"
    )
    parser.add_argument(
        "-f",
        "--function",
        choices=[f.replace("useFunction", "") for f in dir(LightController) if "useFunction" in f],
        help="the name of the function to demo using randomized parameters",
    )
    parser.add_argument(
        "-c",
        "--color",
        choices=[f.replace("useColor", "") for f in dir(LightController) if "useColor" in f],
        help="the name of the color pattern to demo using randomized parameters",
    )
    args = parser.parse_args()

    if args.LED_count is not None:
        PIXEL_COUNT = args.LED_count

    if args.function_duration is not None:
        DURATION = args.function_duration

    if args.function is not None:
        FUNCTIONS = ["useFunction" + args.function]

    if args.color is not None:
        COLORS = ["useColor" + args.color]

    # create the light-function object
    lightControl = LightController(
        ledCount=PIXEL_COUNT,
        pwmGPIOpin=GPIO_PWM_PIN,
        channelDMA=DMA_CHANNEL,
        frequencyPWM=PWM_FREQUENCY,
        channelPWM=PWM_CHANNEL,
        invertSignalPWM=INVERT,
        gamma=GAMMA,
        stripTypeLED=LED_STRIP_TYPE,
        debug=True,
        ledBrightnessFloat=BRIGHTNESS,
    )
    # run the demo!
    try:
        lightControl.demo(DURATION, functionNames=FUNCTIONS, colorNames=COLORS)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        LOGGER.exception(ex)
    lightControl.__del__()
