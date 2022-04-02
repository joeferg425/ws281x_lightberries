"""Example of using LightBerries module with a GUI."""
import time
import multiprocessing
from tkinter.colorchooser import askcolor
import tkinter as tk
from lightberries.array_controller import ArrayController
from lightberries.pixel import Pixel
from lightberries.array_patterns import ArrayPattern

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
# to understand the rest of these arguments read their
# documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0


class LightsProcess:
    """Handles LightBerries functions in a seperate process."""

    def __init__(self, app) -> None:
        """Handles LightBerries functions in a seperate process.

        Args:
            app: the tkinter app
        """
        self.app = app
        self.inQ = multiprocessing.Queue(2)
        self.outQ = multiprocessing.Queue(2)
        self.process = multiprocessing.Process(target=LightsProcess.mainLoop, args=[self, self.inQ, self.outQ])
        self.process.start()

    def __del__(self) -> None:
        """Cleans up ws281X memory."""
        self.process.terminate()
        print("goodbye")

    def mainLoop(self, inQ, _):
        """The main loop.

        Args:
            inQ: multiprocess queue for getting input
            _ : [description]
        """
        try:
            # set up LightBerries controller
            lightControl = ArrayController(
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
            # create virtual LED array
            lightControl.setVirtualLEDArray(ArrayPattern.PixelArrayOff(PIXEL_COUNT))
            lightControl.copyVirtualLedsToWS281X()
            lightControl.refreshLEDs()
            time.sleep(0.05)
            count = PIXEL_COUNT
            color = 0
            duration = 0
            pattern = self.app.patternChoices[0]
            function = self.app.functionChoices[0]
            while True:
                # check for user input
                msg = None
                try:
                    msg = inQ.get()
                except Exception:
                    pass
                if msg is not None:
                    print(msg)
                    if msg[0] == "go":
                        try:
                            # reset LightBerry controller
                            lightControl.reset()
                            # get color pattern method by name, run it
                            getattr(lightControl, pattern)()
                            # get function method by name, run it
                            getattr(lightControl, function)()
                            # set duration
                            lightControl.secondsPerMode = duration
                            # run
                            lightControl.run()
                            # turn lights off when (if) method exits
                            lightControl.off()
                            lightControl.copyVirtualLedsToWS281X()
                            lightControl.refreshLEDs()
                            time.sleep(0.05)
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "color":
                        try:
                            color = msg[1]
                            print("setting color")
                            # turn all LEDs off, then set them to new color
                            lightControl.virtualLEDBuffer[:] *= 0
                            lightControl.virtualLEDBuffer[:] += Pixel(color).array
                            lightControl.copyVirtualLedsToWS281X()
                            lightControl.refreshLEDs()
                            time.sleep(0.05)
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "count":
                        try:
                            count = msg[1]
                            # turn off all LEDs
                            if count < lightControl.privateLEDCount:
                                lightControl.virtualLEDBuffer[:] *= 0
                                lightControl.copyVirtualLedsToWS281X()
                                lightControl.refreshLEDs()
                                time.sleep(0.05)
                            # create new LightBerry controller with new pixel count in
                            # underlying ws281x object
                            lightControl = ArrayController(
                                ledCount=count,
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
                            lightControl.secondsPerMode = duration
                            lightControl.virtualLEDBuffer[:] += Pixel(color).array
                            lightControl.copyVirtualLedsToWS281X()
                            lightControl.refreshLEDs()
                            time.sleep(0.05)
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "duration":
                        try:
                            duration = msg[1]
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "function":
                        try:
                            function = msg[1]
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "pattern":
                        try:
                            pattern = msg[1]
                        except Exception as ex:
                            print(ex)
                time.sleep(0.001)
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            print(ex)
        lightControl.__del__()
        time.sleep(0.05)


class App:
    """The application object for tkinter GUI."""

    def __init__(self) -> None:
        """The application object for tkinter GUI."""
        # create tKinter GUI
        self.root = tk.Tk()

        self.ledCountInt = tk.IntVar()
        self.ledCountlabel = tk.Label(text="LED Count")
        self.ledCountlabel.grid(row=0, column=0)
        self.ledCountslider = tk.Scale(self.root, from_=0, to=500, variable=self.ledCountInt, orient="horizontal")
        self.ledCountslider.grid(row=0, column=1)
        self.ledCountPressed = False

        self.ledCounttext = tk.Entry(self.root, textvariable=self.ledCountInt)
        self.ledCounttext.grid(row=0, column=2)
        self.ledCountInt.set(PIXEL_COUNT)

        self.colorInt = tk.IntVar()
        self.colorString = tk.StringVar()
        self.colorlabel = tk.Label(text="Color")
        self.colorlabel.grid(row=1, column=0)
        self.colorslider = tk.Scale(self.root, from_=0, to=0xFFFFFF, variable=self.colorInt, orient="horizontal")
        self.colorslider.grid(row=1, column=1)
        self.colortext = tk.Entry(self.root, textvariable=self.colorString)
        self.colortext.grid(row=1, column=2)
        self.colorbutton = tk.Button(text="Select Color", command=self.getColor)
        self.colorbutton.grid(row=1, column=3)

        self.functionString = tk.StringVar()
        self.functionChoices = [f for f in dir(ArrayController) if f[:11] == "useFunction"]
        self.functionChoices.sort()
        self.functionString.set(self.functionChoices[0])
        self.functionDropdown = tk.OptionMenu(self.root, self.functionString, *self.functionChoices)
        self.functionDropdown.grid(row=2, column=1)
        self.patternString = tk.StringVar()
        self.patternChoices = [f for f in dir(ArrayController) if f[:8] == "useColor"]
        self.patternChoices.sort()
        self.patternString.set(self.patternChoices[0])
        self.patternDropdown = tk.OptionMenu(self.root, self.patternString, *self.patternChoices)
        self.patternDropdown.grid(row=2, column=2)

        self.durationInt = tk.IntVar()
        self.durationInt.set(10)
        self.durationLabel = tk.Label(text="Duration (Seconds)")
        self.durationLabel.grid(row=3, column=1)
        self.durationText = tk.Entry(self.root, textvariable=self.durationInt)
        self.durationText.grid(row=3, column=2)
        self.buttonGo = tk.Button(self.root, height=1, width=10, text="Go", command=self.goNow)
        self.buttonGo.grid(row=3, column=3)

        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.root.title("LightBerries GUI")

        # create seperate process for controlling lights
        self.lights = LightsProcess(self)

        # connect callbacks to GUI widgets/controls
        self.colorInt.trace(
            "w",
            lambda name, index, mode, var=self.colorInt: self.updateColor(var.get()),
        )
        self.colorString.trace(
            "w",
            lambda name, index, mode, var=self.colorString: self.updateColorHex(var.get()),
        )
        self.ledCountInt.trace(
            "w",
            lambda name, index, mode, var=self.ledCountInt: self.updateLEDCount(var.get()),
        )
        self.functionString.trace(
            "w",
            lambda name, index, mode, var=self.functionString: self.updateFunction(var.get()),
        )
        self.patternString.trace(
            "w",
            lambda name, index, mode, var=self.patternString: self.updatePattern(var.get()),
        )
        self.durationInt.trace(
            "w",
            lambda name, index, mode, var=self.durationInt: self.updateDuration(var.get()),
        )
        try:
            self.lights.inQ.put_nowait(("count", PIXEL_COUNT))
            self.lights.inQ.put_nowait(("duration", self.durationInt.get()))
        except multiprocessing.queues.Full:
            pass
        self.updateColor(0xFF0000)

        # run the GUI thread
        self.root.mainloop()

    def destroy(self) -> None:
        """Destroy this object cleanly."""
        self.root.destroy()
        self.__del__()

    def __del__(self) -> None:
        """Destroy this object cleanly."""
        del self.lights

    def goNow(self):
        """Go."""
        try:
            self.lights.inQ.put_nowait(("go",))
        except multiprocessing.queues.Full:
            pass

    def getColor(self) -> None:
        """Get a color, pass it through multiprocess queue."""
        color = askcolor()
        color = int(color[1][1:], 16)
        self.colorInt.set(color)
        try:
            self.lights.inQ.put_nowait(("color", color))
        except multiprocessing.queues.Full:
            pass

    def updateFunction(self, function: str) -> None:
        """Update the selected function, pass it through multiprocess queue.

        Args:
            function: the function name
        """
        try:
            self.lights.inQ.put_nowait(("function", function))
        except multiprocessing.queues.Full:
            pass

    def updatePattern(self, pattern: str) -> None:
        """Update the selected pattern, pass it through multiprocess queue.

        Args:
            pattern: the pattern name
        """
        try:
            self.lights.inQ.put_nowait(("pattern", pattern))
        except multiprocessing.queues.Full:
            pass

    def updateDuration(self, duration: float) -> None:
        """Update the selected duration, pass it through multiprocess queue.

        Args:
            duration: the duration in seconds
        """
        try:
            self.lights.inQ.put_nowait(("duration", duration))
        except multiprocessing.queues.Full:
            pass

    def updateLEDCount(self, count: int) -> None:
        """Update the selected LED count, pass it through multiprocess queue.

        Args:
            count: the LED count
        """
        try:
            count = int(count)
            self.lights.inQ.put_nowait(("count", count))
        except multiprocessing.queues.Full:
            pass

    def updateColor(self, color: int) -> None:
        """Update color of all LEDs.

        Args:
            color: the LED colors
        """
        if self.root.focus_get() != self.colortext:
            self.colorString.set(f"{color:06X}")
        try:
            self.lights.inQ.put_nowait(("color", color))
        except multiprocessing.queues.Full:
            pass

    def updateColorHex(self, color: str) -> None:
        """Update color of all LEDs.

        Args:
            color: the LED colors
        """
        color = int(color, 16)
        self.colorInt.set(color)


if __name__ == "__main__":
    theApp = App()
    del theApp
