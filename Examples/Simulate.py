#!/usr/bin/python3
"""Example of syncing lights to audio."""
import time
import multiprocessing
import multiprocessing.queues
import tkinter as tk
import matplotlib.pyplot as plt
from numpy import double
from LightBerries.LightArrayControls import LightArrayController
from LightBerries.LightPixels import Pixel


class LightOutput:
    """Outputs audio FFT to light controller object."""

    def __init__(
        self,
        lightQ: multiprocessing.Queue,
        plotQ: multiprocessing.Queue,
        tkQ: multiprocessing.Queue,
        exitQ: multiprocessing.Queue,
    ) -> None:
        """Outputs audio FFT to light controller object.

        Args:
            lightQ: multiprocessing queue for receiving data
            plotQ: multiprocessing queue for sending data
            tkQ: multiprocessing queue for sending data
            exitQ: multiprocessing queue for sending data
        """
        self.lightQ = lightQ
        self.plotQ = plotQ
        self.tkQ = tkQ
        self.exitQ = exitQ
        self.delay = 0.1
        self.lightController = None
        self.func = ""
        self.colr = ""
        # run routine
        self.run()

    def update(self):
        """Update the gui."""
        # print("led refresh")
        self.plotQ.put(self.lightController.virtualLEDArray)
        time.sleep(self.delay)

    def run(self):
        """Run the process."""
        try:
            ledCount = None
            while ledCount is None:
                try:
                    ledCount = self.lightQ.get_nowait()
                except multiprocessing.queues.Empty:
                    pass
            self.lightController = LightArrayController(
                ledCount,
                18,
                10,
                800000,
                simulate=True,
                refreshCallback=lambda: self.update(),
            )
            # print("started lights")
            while True:
                try:
                    msg = self.lightQ.get_nowait()
                    # print(msg)
                    if isinstance(msg, int):
                        self.lightController.secondsPerMode = msg
                    if isinstance(msg, (float, double)):
                        self.delay = msg
                    elif isinstance(msg, str):
                        if len(msg) > 8 and msg[:8] == "useColor":
                            # print(msg)
                            self.colr = msg
                        elif len(msg) > 11 and msg[:11] == "useFunction":
                            # print(msg)
                            self.func = msg
                        elif len(msg) > 1 and msg == "go":
                            # print("run it")
                            self.lightController.reset()
                            self.lightController.off()
                            self.lightController.refreshLEDs()
                            getattr(self.lightController, self.colr)()
                            getattr(self.lightController, self.func)()
                            self.tkQ.put("running")
                            self.lightController.run()
                            self.tkQ.put("done")
                except multiprocessing.queues.Empty:
                    pass
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            print(f"Error in {LightOutput.__name__}: {str(ex)}")
        finally:
            # clean up the LightBerry object
            self.lightController.off()
            self.lightController.copyVirtualLedsToWS281X()
            self.lightController.refreshLEDs()
            # pause for object destruction
            time.sleep(0.2)
            # put any data in queue, this will signify "exit" status
            self.exitQ.put("quit")
            # double-check deletion
            del self.lightController


class PlotOutput:
    """Plots audio FFT to matplotlib's pyplot graphic."""

    def __init__(
        self,
        plotQ: multiprocessing.Queue,
        tkQ: multiprocessing.Queue,
        exitQ: multiprocessing.Queue,
    ) -> None:
        """Plots audio FFT to matplotlib's pyplot graphic.

        Args:
            plotQ: multiprocessing queue for receiving data
            tkQ: multiprocessing queue for sending data
            exitQ: multiprocessing queue for sending data
        """
        self.plotQ = plotQ
        self.tkQ = tkQ
        self.exitQ = exitQ
        self.buttonCallback = None
        plt.ion()
        self.run()

    def run(self):
        """Run the process."""
        try:
            while True:
                try:
                    # try to get new data
                    array = self.plotQ.get_nowait()
                    self.tkQ.put([Pixel(rgb).hexstr for rgb in array])
                except multiprocessing.queues.Empty:
                    pass
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            print(f"Error in {PlotOutput.__name__}: {str(ex)}")
        finally:
            self.exitQ.put("quit")


class App:
    """The application for tkinter."""

    def __init__(self) -> None:
        """The application for tkinter."""
        # create tKinter GUI. This GUI could really use some help
        self.lightQ: multiprocessing.Queue = multiprocessing.Queue()
        self.plotQ: multiprocessing.Queue = multiprocessing.Queue()
        self.tkQ: multiprocessing.Queue = multiprocessing.Queue()
        self.exitQ: multiprocessing.Queue = multiprocessing.Queue()
        # create process objects
        self.lightProcess = multiprocessing.Process(
            target=LightOutput,
            args=(
                self.lightQ,
                self.plotQ,
                self.tkQ,
                self.exitQ,
            ),
        )
        self.guiProcess = multiprocessing.Process(
            target=PlotOutput,
            args=(
                self.plotQ,
                self.tkQ,
                self.exitQ,
            ),
        )
        # start the selected process
        self.lightProcess.start()
        self.guiProcess.start()

        self.ledCount = None
        self.buttons = []
        self.running = False

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
        # self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(1, weight=1)
        self.mainFrame.columnconfigure(2, weight=1)
        self.mainFrame.columnconfigure(3, weight=1)
        self.mainFrame.columnconfigure(4, weight=1)

        self.ledCountInt = tk.IntVar()
        self.ledCountlabel = tk.Label(
            self.mainFrame,
            text="LED Count",
        )
        self.ledCountlabel.grid(
            row=0,
            column=0,
        )

        self.ledCounttext = tk.Entry(
            self.mainFrame,
            textvariable=self.ledCountInt,
        )
        self.ledCounttext.grid(
            row=0,
            column=1,
        )
        self.ledCountInt.set(100)

        self.functionString = tk.StringVar()
        self.functionChoices = [f for f in dir(LightArrayController) if f[:11] == "useFunction"]
        self.functionChoices.sort()
        self.functionString.set(self.functionChoices[0])
        self.functionDropdown = tk.OptionMenu(
            self.mainFrame,
            self.functionString,
            *self.functionChoices,
        )
        self.functionDropdown.grid(
            row=0,
            column=2,
        )

        self.patternString = tk.StringVar()
        self.patternChoices = [f for f in dir(LightArrayController) if f[:8] == "useColor"]
        self.patternChoices.sort()
        self.patternString.set(self.patternChoices[0])
        self.patternDropdown = tk.OptionMenu(
            self.mainFrame,
            self.patternString,
            *self.patternChoices,
        )
        self.patternDropdown.grid(
            row=0,
            column=3,
        )

        self.durationInt = tk.IntVar()
        self.durationInt.set(10)
        self.durationLabel = tk.Label(
            self.mainFrame,
            text="Test Duration (Seconds)",
        )
        self.durationLabel.grid(
            row=0,
            column=4,
        )
        self.durationText = tk.Entry(
            self.mainFrame,
            textvariable=self.durationInt,
        )
        self.durationText.grid(
            row=0,
            column=5,
        )

        self.delayFloat = tk.DoubleVar()
        self.delayFloat.set(0.05)
        self.delayLabel = tk.Label(
            self.mainFrame,
            text="Refresh Delay (Seconds)",
        )
        self.delayLabel.grid(
            row=0,
            column=6,
        )
        self.delayText = tk.Entry(
            self.mainFrame,
            textvariable=self.delayFloat,
        )
        self.delayText.grid(
            row=0,
            column=7,
        )

        self.buttonGo = tk.Button(
            self.mainFrame,
            height=1,
            width=10,
            text="Go",
            command=self.configureLightBerries,
        )
        self.buttonGo.grid(
            row=0,
            column=8,
        )

        self.root.bind("<Return>", lambda event: self.configureLightBerries())

        self.buttonFrame = tk.Frame(
            self.mainFrame,
        )
        self.buttonFrame.grid(
            row=1,
            column=0,
            columnspan=9,
            sticky="news",
        )

        self.root.protocol("WM_DELETE_WINDOW", self.destroy)

        self.root.title("LightBerries LED GUI Simulator (function parameters not included)")
        self.root.after(1, self.checkQ)

        self.root.mainloop()

    def checkQ(self):
        """Method for checking whether other processes have sent us data."""
        self.root.after(1, self.checkQ)
        try:
            data = self.tkQ.get_nowait()
            if isinstance(data, str):
                if data == "running":
                    self.running = True
                    self.ledCounttext["state"] = "disabled"
                    self.buttonGo["state"] = "disabled"
                elif data == "done":
                    self.running = False
                    self.ledCounttext["state"] = "normal"
                    self.buttonGo["state"] = "normal"
            else:
                for index, btn in enumerate(self.buttons):
                    btn.configure(bg="#" + data[index])
            # print(f"app got data: {len(data)}")
        except multiprocessing.queues.Empty:
            pass

    def onConfigure(self):
        """Configure the convas widget."""
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def configureLightBerries(self):
        """Configure LightBerries."""
        # print("configuring")
        if self.ledCount is None:
            ledCount = int(self.ledCountInt.get())
            for column in range(ledCount):
                self.buttonFrame.columnconfigure(column, weight=1)
                btn = tk.Button(self.buttonFrame, bg="black", fg="white", width=1, height=1)
                btn.grid(
                    row=1,
                    column=column,
                    sticky="nw",
                )
                self.buttons.append(btn)
            self.lightQ.put_nowait(ledCount)
            self.ledCount = ledCount
        # print("sending data")
        if self.running is False:
            self.lightQ.put(self.durationInt.get())
            self.lightQ.put(self.delayFloat.get())
            self.lightQ.put(self.patternString.get())
            self.lightQ.put(self.functionString.get())
            self.lightQ.put("go")

    def destroy(self) -> None:
        """Destroy this object."""
        self.root.destroy()
        self.__del__()

    def __del__(self) -> None:
        """Destroy the object cleanly."""
        pass


if __name__ == "__main__":
    theApp = App()
    del theApp
