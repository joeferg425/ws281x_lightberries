#!/usr/bin/python3
"""Example of using LightBerries module functions with a GUI.

Use GUI to interact with individual LEDs.
"""
import time
import multiprocessing
import multiprocessing.queues
from tkinter.colorchooser import askcolor
import tkinter as tk
import LightBerries.LightPixels
from LightBerries.LightArrayControls import LightArrayController
from LightBerries.LightPixels import Pixel
from LightBerries.LightArrayPatterns import ConvertPixelArrayToNumpyArray, SolidColorArray


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
    """Handles LightBerries functions in a seperate process."""

    selfObject = None
    appObject = None

    def __init__(self, app) -> None:
        """Handles LightBerries functions in a seperate process.

        Args:
            app: the tkinter app
        """
        LightsProcess.selfObject = self
        LightsProcess.appObject = app
        self.inQ = multiprocessing.Queue(2)
        self.outQ = multiprocessing.Queue(2)
        self.process = multiprocessing.Process(target=LightsProcess.mainLoop, args=[self.inQ, self.outQ])
        self.process.start()

    def __del__(self) -> None:
        """Clean up memory."""
        self.process.terminate()

    @classmethod
    def mainLoop(cls, inQ, _):
        """The main loop.

        Args:
            inQ: multiprocess queue for getting input
            _ : [description]
        """
        try:
            # create LightBerry controller
            lightControl = LightArrayController(
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
            lightControl.setVirtualLEDBuffer(
                ConvertPixelArrayToNumpyArray(
                    SolidColorArray(arrayLength=PIXEL_COUNT, color=LightBerries.LightPixels.PixelColors.OFF)
                )
            )
            lightControl.copyVirtualLedsToWS281X()
            lightControl.refreshLEDs()

            # run loop forever
            while True:
                # check for new user input
                msg = None
                try:
                    msg = inQ.get()
                except Exception:
                    pass
                if msg is not None:
                    print(msg)
                    if msg[0] == "color":
                        try:
                            index, color = msg[1:]
                            print("setting color")
                            lightControl.virtualLEDBuffer[index] = Pixel(
                                color, order=LightBerries.LightPixels.EnumLEDOrder.RGB
                            ).array
                            lightControl.copyVirtualLedsToWS281X()
                            lightControl.refreshLEDs()
                            time.sleep(0.05)
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
    """The application for tkinter."""

    def __init__(self) -> None:
        """The application for tkinter."""
        # create tKinter GUI. This GUI could really use some help
        self.root = tk.Tk()

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side=tk.RIGHT, fill="both", expand=True)

        self.scrollbarY = tk.Scrollbar(self.canvas, command=self.canvas.yview, orient=tk.VERTICAL)
        self.scrollbarY.pack(side=tk.RIGHT, fill="y")
        self.scrollbarX = tk.Scrollbar(self.canvas, command=self.canvas.xview, orient=tk.HORIZONTAL)
        self.scrollbarX.pack(side=tk.BOTTOM, fill="y")

        self.mainFrame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.mainFrame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbarY.set)
        self.canvas.configure(xscrollcommand=self.scrollbarX.set)

        self.mainFrame.pack(fill="both", anchor=tk.NW, expand=True)
        self.mainFrame.rowconfigure(1, weight=1)
        self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(1, weight=1)
        self.mainFrame.columnconfigure(2, weight=1)
        self.mainFrame.columnconfigure(3, weight=1)
        self.mainFrame.columnconfigure(4, weight=1)
        self.mainFrame.columnconfigure(5, weight=1)
        self.mainFrame.columnconfigure(6, weight=1)

        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.bind("<Configure>", lambda _: self.onConfigure())

        self.rowInt = tk.IntVar(value=3)
        self.rowString = tk.StringVar()
        self.columnInt = tk.IntVar(value=3)
        self.columnString = tk.StringVar()

        self.rowlabel = tk.Label(
            self.mainFrame,
            text="Row Count",
        )
        self.rowlabel.grid(
            row=0,
            column=0,
            sticky="news",
        )

        self.rowInput = tk.Entry(
            self.mainFrame,
            textvariable=self.rowString,
        )
        self.rowInput.grid(
            row=0,
            column=1,
            sticky="news",
        )
        self.rowString.set(str(self.rowInt.get()))

        self.columnLabel = tk.Label(
            self.mainFrame,
            text="Column Count",
        )
        self.columnLabel.grid(
            row=0,
            column=2,
            sticky="news",
        )

        self.columnInput = tk.Entry(
            self.mainFrame,
            textvariable=self.columnString,
        )
        self.columnInput.grid(
            row=0,
            column=3,
            sticky="news",
        )
        self.columnString.set(str(self.columnInt.get()))

        self.configureButton = tk.Button(
            self.mainFrame,
            text="Configure",
            command=self.configureLightBerries,
        )
        self.configureButton.grid(
            row=0,
            column=4,
            sticky="news",
        )
        self.root.bind("<Return>", lambda event: self.configureLightBerries())

        self.leftClickColorBtn = tk.Button(
            self.mainFrame, bg="black", fg="white", text="Left-Click\nColor", width=5, height=2
        )
        self.leftClickColorBtn.grid(
            row=0,
            column=5,
            sticky="news",
        )
        self.leftClickColorBtn.ledIndex = None
        self.leftClickColorBtn.bind("<Button-1>", self.getColor)

        self.rightClickColorBtn = tk.Button(
            self.mainFrame, bg="black", fg="white", text="Right-Click\nColor", width=5, height=2
        )
        self.rightClickColorBtn.grid(
            row=0,
            column=6,
            sticky="news",
        )
        self.rightClickColorBtn.ledIndex = None
        self.rightClickColorBtn.bind("<Button-1>", self.getColor)
        self.rightClickColorBtn.bind("<Button-3>", self.getColor)

        self.buttonFrame = tk.Frame(
            self.mainFrame,
        )
        self.buttonFrame.grid(
            row=1,
            column=0,
            columnspan=5,
            sticky="news",
        )

        self.lights = LightsProcess(self)

        self.root.protocol("WM_DELETE_WINDOW", self.destroy)

        self.root.title("LightBerries Pixel Color Chooser")
        self.root.mainloop()

    def onConfigure(self):
        """Configure the convas widget."""
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def configureLightBerries(self):
        """Configure LightBerries."""
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
                    btn.bind("<Button-1>", self.getColor)
                    btn.bind("<Button-3>", self.getColor2)
                    btn.grid(column=column, row=row, sticky="nw")
                    btn.ledIndex = counter
                    counter += 1
            self.configureButton["state"] = "disabled"
        except Exception:
            pass

    def destroy(self) -> None:
        """Destroy this object."""
        self.root.destroy()
        self.__del__()

    def getColor(self, event) -> None:
        """Get a color from user, pass it to LightBerries.

        Args:
            event: tkinter widget event object
        """
        if event.widget.ledIndex is None:
            color = askcolor(event.widget["background"])
            if color is not None:
                color = int(color[1][1:], 16)
                colorHex = f"#{color:06X}"
                event.widget.configure(bg=colorHex)
                invertColor = 0xFFFFFF - color
                invertColorHex = "#" + f"{invertColor:06X}"[-6:]
                event.widget.configure(fg=invertColorHex)
        else:
            color = self.leftClickColorBtn["background"]
            event.widget.configure(bg=color)
            invertColor = self.leftClickColorBtn["foreground"]
            event.widget.configure(fg=invertColor)
            try:
                color = int(color[1:], 16)
                self.lights.inQ.put_nowait(("color", event.widget.ledIndex, color))
            except multiprocessing.queues.Full:
                pass

    def getColor2(self, event) -> None:
        """Get a color from user, pass it to LightBerries.

        Args:
            event: tkinter widget event object
        """
        color = self.rightClickColorBtn["background"]
        event.widget.configure(bg=color)
        invertColor = self.rightClickColorBtn["foreground"]
        event.widget.configure(fg=invertColor)
        try:
            color = int(color[1:], 16)
            self.lights.inQ.put_nowait(("color", event.widget.ledIndex, color))
        except multiprocessing.queues.Full:
            pass

    def __del__(self) -> None:
        """Destroy the object cleanly."""
        del self.lights


if __name__ == "__main__":
    theApp = App()
    del theApp
