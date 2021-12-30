#!/usr/bin/python3
"""example of using this module's functions with a GUI"""
import time
import multiprocessing
import multiprocessing.queues
from tkinter.colorchooser import askcolor
import tkinter as tk

from numpy import true_divide
import LightBerries.LightPixels
from LightBerries.LightControl import LightController
from LightBerries.LightPixels import Pixel
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray, PixelArray, SolidColorArray


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
LightBerries.LightPixels.DEFAULT_PIXEL_ORDER = LightBerries.LightPixels.EnumLEDOrder.RGB


class LightsProcess:
    """handles lights in a seperate process"""

    selfObject = None
    appObject = None

    def __init__(self, app):
        LightsProcess.selfObject = self
        LightsProcess.appObject = app
        self.inQ = multiprocessing.Queue(2)
        self.outQ = multiprocessing.Queue(2)
        self.process = multiprocessing.Process(target=LightsProcess.lupe, args=[self.inQ, self.outQ])
        self.process.start()

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
            lightControl.setVirtualLEDArray(
                ConvertPixelArrayToNumpyArray(
                    SolidColorArray(arrayLength=PIXEL_COUNT, color=LightBerries.LightPixels.PixelColors.OFF)
                )
            )
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
                    if msg[0] == "color":
                        try:
                            index, color = msg[1:]
                            print("setting color")
                            # lightControl.virtualLEDArray[:] *= 0
                            lightControl.virtualLEDArray[index] += Pixel(
                                color, order=LightBerries.LightPixels.EnumLEDOrder.RGB
                            ).array
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

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side=tk.RIGHT, fill="both", expand=True)

        self.scrollbarY = tk.Scrollbar(self.canvas, command=self.canvas.yview, orient=tk.VERTICAL)
        self.scrollbarY.pack(side=tk.RIGHT, fill="y")
        self.scrollbarX = tk.Scrollbar(self.canvas, command=self.canvas.xview, orient=tk.HORIZONTAL)
        self.scrollbarX.pack(side=tk.BOTTOM, fill="y")

        self.mainFrame = tk.Frame(self.canvas)
        # self.mainFrame = tk.Frame(self.canvas, width=600, height=400)
        self.canvas.create_window((0, 0), window=self.mainFrame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbarY.set)
        self.canvas.configure(xscrollcommand=self.scrollbarX.set)

        self.mainFrame.pack(fill="both", anchor=tk.NW, expand=True)
        # self.mainFrame.grid(row=0, column=0, sticky="news")
        self.mainFrame.rowconfigure(1, weight=1)
        self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(1, weight=1)
        self.mainFrame.columnconfigure(2, weight=1)
        self.mainFrame.columnconfigure(3, weight=1)
        self.mainFrame.columnconfigure(4, weight=1)

        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.bind("<Configure>", lambda event: self.on_configure(event))

        self.rowInt = tk.IntVar(value=3)
        self.rowString = tk.StringVar()
        self.columnInt = tk.IntVar(value=3)
        self.columnString = tk.StringVar()

        self.rowlabel = tk.Label(
            self.mainFrame,
            text="Row Count",
        )
        # self.rowlabel.min
        self.rowlabel.grid(
            row=0,
            column=0,
            sticky="news",
        )

        self.rowInput = tk.Entry(self.mainFrame, textvariable=self.rowString).grid(
            row=0,
            column=1,
            sticky="news",
        )
        self.rowString.set(str(self.rowInt.get()))

        self.columnLabel = tk.Label(self.mainFrame, text="Column Count",).grid(
            row=0,
            column=2,
            sticky="news",
        )

        self.columnInput = tk.Entry(self.mainFrame, textvariable=self.columnString,).grid(
            row=0,
            column=3,
            sticky="news",
        )
        self.columnString.set(str(self.columnInt.get()))

        self.configureButton = tk.Button(
            self.mainFrame,
            text="Configure",
            command=self.configure,
        )
        self.configureButton.grid(row=0, column=4, sticky="news")

        self.buttonFrame = tk.Frame(self.mainFrame)
        self.buttonFrame.grid(row=1, column=0, columnspan=5, sticky="news")

        self.lights = LightsProcess(self)

        self.root.protocol("WM_DELETE_WINDOW", self.destroy)

        self.root.title("Color Chooser")
        self.root.mainloop()

    def on_configure(self, event):
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def configure(self):
        counter = 0
        try:
            for row in range(int(self.rowString.get())):
                self.buttonFrame.rowconfigure(row, weight=1)
                for column in range(int(self.columnString.get())):
                    self.buttonFrame.columnconfigure(column, weight=1)
                    btn = tk.Button(
                        self.buttonFrame, bg="black", fg="white", text=str(counter), width=5, height=2
                    )
                    btn.grid(
                        row=row,
                        column=column,
                        sticky="nw",
                    )
                    btn.bind("<Button-1>", lambda event: self.getColor(event, btn))
                    btn.grid(column=column, row=row, sticky="nw")
                    btn.ledIndex = counter
                    counter += 1
            self.configureButton["state"] = "disabled"
        except:
            pass

    def destroy(self):
        """destroy this object"""
        self.root.destroy()
        self.__del__()

    def getColor(self, event, btn):
        """get a color"""
        print(event.widget.ledIndex)
        color = askcolor(event.widget["background"])
        if color is not None:
            color = int(color[1][1:], 16)
            hx = "#{:06X}".format(color)
            event.widget.configure(bg=hx)
            hx = "#" + "{:06X}".format(0xFFFFFF - color)[-6:]
            event.widget.configure(fg=hx)
            try:
                self.lights.inQ.put_nowait(("color", event.widget.ledIndex, color))
            except multiprocessing.queues.Full:
                pass

    def __del__(self):
        del self.lights


if __name__ == "__main__":
    app = App()
    del app
