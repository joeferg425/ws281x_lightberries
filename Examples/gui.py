import tkinter as tk
from LightBerries.LightControl import LightController
from LightBerries.Pixels import Pixel
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray, PixelArray
from tkinter.colorchooser import *
import time
import multiprocessing

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
# to understand the rest of these arguments read their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
GAMMA = None
LED_STRIP_TYPE = None
INVERT = False
PWM_CHANNEL = 0


class LightsProcess:
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
    def lupe(cls, inQ, outQ):
        try:
            lf = LightController(
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
            lf._setVirtualLEDArray(ConvertPixelArrayToNumpyArray(PixelArray(PIXEL_COUNT)))
            lf._copyVirtualLedsToWS281X()
            lf._refreshLEDs()
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
                except:
                    pass
                if not msg is None:
                    print(msg)
                    if msg[0] == "go":
                        try:
                            lf.reset()
                            getattr(lf, pattern)()
                            getattr(lf, function)()
                            lf.secondsPerMode = duration
                            lf.run()
                            lf._off()
                            lf._copyVirtualLedsToWS281X()
                            lf._refreshLEDs()
                            time.sleep(0.05)
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "color":
                        try:
                            color = msg[1]
                            print("setting color")
                            lf._VirtualLEDArray[:] *= 0
                            lf._VirtualLEDArray[:] += Pixel(color).array
                            lf._copyVirtualLedsToWS281X()
                            lf._refreshLEDs()
                            time.sleep(0.05)
                        except Exception as ex:
                            print(ex)
                    elif msg[0] == "count":
                        try:
                            count = msg[1]
                            if count < lf.__LEDCount:
                                lf._VirtualLEDArray[:] *= 0
                                lf._copyVirtualLedsToWS281X()
                                lf._refreshLEDs()
                                time.sleep(0.05)
                            lf = LightController(
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
                            lf.secondsPerMode = duration
                            lf._VirtualLEDArray[:] += Pixel(color).array
                            lf._copyVirtualLedsToWS281X()
                            lf._refreshLEDs()
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
        lf.__del__()
        time.sleep(0.05)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.lights = LightsProcess()

        self.LEDCountInt = tk.IntVar()
        self.LEDCountInt.trace(
            "w", lambda name, index, mode, var=self.LEDCountInt: self.updateLEDCount(var.get())
        )
        self.LEDCountlabel = tk.Label(text="LED Count")
        self.LEDCountlabel.grid(row=0, column=0)
        self.LEDCountslider = tk.Scale(
            self.root, from_=0, to=500, variable=self.LEDCountInt, orient="horizontal"
        )
        self.LEDCountslider.grid(row=0, column=1)
        self.LEDCountPressed = False

        self.LEDCounttext = tk.Entry(self.root, textvariable=self.LEDCountInt)
        self.LEDCounttext.grid(row=0, column=2)
        self.LEDCountInt.set(PIXEL_COUNT)
        try:
            self.lights.inQ.put_nowait(("count", PIXEL_COUNT))
        except multiprocessing.queues.Full:
            pass

        self.ColorInt = tk.IntVar()
        self.ColorString = tk.StringVar()
        self.ColorInt.trace("w", lambda name, index, mode, var=self.ColorInt: self.updateColor(var.get()))
        self.ColorString.trace(
            "w", lambda name, index, mode, var=self.ColorString: self.updateColorHex(var.get())
        )
        self.Colorlabel = tk.Label(text="Color")
        self.Colorlabel.grid(row=1, column=0)
        self.Colorslider = tk.Scale(
            self.root, from_=0, to=0xFFFFFF, variable=self.ColorInt, orient="horizontal"
        )
        self.Colorslider.grid(row=1, column=1)
        self.Colortext = tk.Entry(self.root, textvariable=self.ColorString)
        self.Colortext.grid(row=1, column=2)
        self.Colorbutton = tk.Button(text="Select Color", command=self.getColor)
        self.Colorbutton.grid(row=1, column=3)
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
        self.buttonGo = tk.Button(self.root, height=1, width=10, text="Go", command=self.go)
        self.buttonGo.grid(row=3, column=3)
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        try:
            self.lights.inQ.put_nowait(("duration", self.durationInt.get()))
        except multiprocessing.queues.Full:
            pass

        self.root.title("Color Chooser")

        self.root.mainloop()

    def destroy(self):
        self.root.destroy()
        self.__del__()

    def __del__(self):
        del self.lights

    def go(self):
        try:
            self.lights.inQ.put_nowait(("go",))
        except multiprocessing.queues.Full:
            pass

    def getColor(self):
        color = askcolor()
        color = int(color[1][1:], 16)
        self.ColorInt.set(color)
        try:
            self.lights.inQ.put_nowait(("color", color))
        except multiprocessing.queues.Full:
            pass

    def updateFunction(self, function):
        try:
            self.lights.inQ.put_nowait(("function", function))
        except multiprocessing.queues.Full:
            pass

    def updatePattern(self, pattern):
        try:
            self.lights.inQ.put_nowait(("pattern", pattern))
        except multiprocessing.queues.Full:
            pass

    def updateDuration(self, duration):
        try:
            self.lights.inQ.put_nowait(("duration", duration))
        except multiprocessing.queues.Full:
            pass

    def updateLEDCount(self, count):
        try:
            count = int(count)
            self.lights.inQ.put_nowait(("count", count))
        except multiprocessing.queues.Full:
            pass

    def updateColor(self, color):
        if self.root.focus_get() != self.Colortext:
            self.ColorString.set("{:06X}".format(color))
        try:
            self.lights.inQ.put_nowait(("color", color))
        except multiprocessing.queues.Full:
            pass

    def updateColorHex(self, color):
        color = int(color, 16)
        self.ColorInt.set(color)


if __name__ == "__main__":
    app = App()
    del app
