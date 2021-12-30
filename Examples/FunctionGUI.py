"""example of using this module with a GUI"""
import time
import multiprocessing
from tkinter.colorchooser import askcolor
import tkinter as tk
from LightBerries.LightControl import LightController
from LightBerries.Pixels import Pixel
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray, PixelArray

# the number of pixels in the light string
PIXEL_COUNT = 196
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
    """handles lights in a seperate process"""

    def __init__(self):
        self.inQ = multiprocessing.Queue(2)
        self.outQ = multiprocessing.Queue(2)
        self.process = multiprocessing.Process(target=LightsProcess.lupe, args=[self.inQ, self.outQ])
        # self.process = multiprocessing.Process(target=App)
        self.process.start()
        # LightsProcess.lupe(1, 2)

    def __del__(self):
        self.process.terminate()
        print("goodbye")

    @classmethod
    def lupe(cls, inQ, _):
        """loooop"""
        try:
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
            # print(dir(lf))
            lightControl.setVirtualLEDArray(ConvertPixelArrayToNumpyArray(PixelArray(PIXEL_COUNT)))
            lightControl.copyVirtualLedsToWS281X()
            lightControl.refreshLEDs()
            time.sleep(0.05)
            count = PIXEL_COUNT
            color = 0
            duration = 0
            pattern = ""
            function = ""
            while True:
                msg = None
                try:
                    msg = inQ.get()
                except Exception:
                    pass
                if not msg is None:
                    print(msg)
                    if msg[0] == "go":
                        try:
                            lightControl.reset()
                            getattr(lightControl, pattern)()
                            getattr(lightControl, function)()
                            lightControl.secondsPerMode = duration
                            lightControl.run()
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
                            lightControl.virtualLEDArray[:] *= 0
                            lightControl.virtualLEDArray[:] += Pixel(color).array
                            lightControl.copyVirtualLedsToWS281X()
                            lightControl.refreshLEDs()
                            time.sleep(0.05)
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "count":
                        try:
                            count = msg[1]
                            if count < lightControl.privateLEDCount:
                                lightControl.virtualLEDArray[:] *= 0
                                lightControl.copyVirtualLedsToWS281X()
                                lightControl.refreshLEDs()
                                time.sleep(0.05)
                            lightControl = LightController(
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
                            lightControl.virtualLEDArray[:] += Pixel(color).array
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
    """the application for tkinter"""

    def __init__(self):
        self.root = tk.Tk()
        self.lights = LightsProcess()

        self.ledCountInt = tk.IntVar()
        self.ledCountInt.trace(
            "w", lambda name, index, mode, var=self.ledCountInt: self.updateLEDCount(var.get())
        )
        self.ledCountlabel = tk.Label(text="LED Count")
        self.ledCountlabel.grid(row=0, column=0)
        self.ledCountslider = tk.Scale(
            self.root, from_=0, to=500, variable=self.ledCountInt, orient="horizontal"
        )
        self.ledCountslider.grid(row=0, column=1)
        self.ledCountPressed = False

        self.ledCounttext = tk.Entry(self.root, textvariable=self.ledCountInt)
        self.ledCounttext.grid(row=0, column=2)
        self.ledCountInt.set(PIXEL_COUNT)
        try:
            self.lights.inQ.put_nowait(("count", PIXEL_COUNT))
        except multiprocessing.queues.Full:
            pass

        self.colorInt = tk.IntVar()
        self.colorString = tk.StringVar()
        self.colorInt.trace("w", lambda name, index, mode, var=self.colorInt: self.updateColor(var.get()))
        self.colorString.trace(
            "w", lambda name, index, mode, var=self.colorString: self.updateColorHex(var.get())
        )
        self.colorlabel = tk.Label(text="Color")
        self.colorlabel.grid(row=1, column=0)
        self.colorslider = tk.Scale(
            self.root, from_=0, to=0xFFFFFF, variable=self.colorInt, orient="horizontal"
        )
        self.colorslider.grid(row=1, column=1)
        self.colortext = tk.Entry(self.root, textvariable=self.colorString)
        self.colortext.grid(row=1, column=2)
        self.colorbutton = tk.Button(text="Select Color", command=self.getColor)
        self.colorbutton.grid(row=1, column=3)
        self.updateColor(0xFF0000)

        self.functionString = tk.StringVar()
        self.functionString.trace(
            "w", lambda name, index, mode, var=self.functionString: self.updateFunction(var.get())
        )
        self.functionChoices = [f for f in dir(LightController) if f[:8] == "function"]
        self.functionChoices.sort()
        self.functionString.set(self.functionChoices[0])
        self.functionDropdown = tk.OptionMenu(self.root, self.functionString, *self.functionChoices)
        self.functionDropdown.grid(row=2, column=1)
        self.patternString = tk.StringVar()
        self.patternString.trace(
            "w", lambda name, index, mode, var=self.patternString: self.updatePattern(var.get())
        )
        self.patternChoices = [f for f in dir(LightController) if f[:8] == "useColor"]
        self.patternChoices.sort()
        self.patternString.set(self.patternChoices[0])
        self.patternDropdown = tk.OptionMenu(self.root, self.patternString, *self.patternChoices)
        self.patternDropdown.grid(row=2, column=2)

        self.durationInt = tk.IntVar()
        self.durationInt.set(10)
        self.durationInt.trace(
            "w", lambda name, index, mode, var=self.durationInt: self.updateDuration(var.get())
        )
        self.durationLabel = tk.Label(text="Duration (Seconds)")
        self.durationLabel.grid(row=3, column=1)
        self.durationText = tk.Entry(self.root, textvariable=self.durationInt)
        self.durationText.grid(row=3, column=2)
        self.buttonGo = tk.Button(self.root, height=1, width=10, text="Go", command=self.goNow)
        self.buttonGo.grid(row=3, column=3)
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        try:
            self.lights.inQ.put_nowait(("duration", self.durationInt.get()))
        except multiprocessing.queues.Full:
            pass

        self.root.title("Color Chooser")

        self.root.mainloop()

    def destroy(self):
        """destroy this object"""
        self.root.destroy()
        self.__del__()

    def __del__(self):
        del self.lights

    def goNow(self):
        """go"""
        try:
            self.lights.inQ.put_nowait(("go",))
        except multiprocessing.queues.Full:
            pass

    def getColor(self):
        """get a color"""
        color = askcolor()
        color = int(color[1][1:], 16)
        self.colorInt.set(color)
        try:
            self.lights.inQ.put_nowait(("color", color))
        except multiprocessing.queues.Full:
            pass

    def updateFunction(self, function):
        """update the function"""
        try:
            self.lights.inQ.put_nowait(("function", function))
        except multiprocessing.queues.Full:
            pass

    def updatePattern(self, pattern):
        """update the color pattern"""
        try:
            self.lights.inQ.put_nowait(("pattern", pattern))
        except multiprocessing.queues.Full:
            pass

    def updateDuration(self, duration):
        """update the duration"""
        try:
            self.lights.inQ.put_nowait(("duration", duration))
        except multiprocessing.queues.Full:
            pass

    def updateLEDCount(self, count):
        """update the number of LEDs"""
        try:
            count = int(count)
            self.lights.inQ.put_nowait(("count", count))
        except multiprocessing.queues.Full:
            pass

    def updateColor(self, color):
        """update color"""
        if self.root.focus_get() != self.colortext:
            self.colorString.set(f"{color:06X}")
        try:
            self.lights.inQ.put_nowait(("color", color))
        except multiprocessing.queues.Full:
            pass

    def updateColorHex(self, color):
        """update color in hex"""
        color = int(color, 16)
        self.colorInt.set(color)


if __name__ == "__main__":
    app = App()
    del app
