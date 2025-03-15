#!/usr/bin/python3
"""Example of syncing lights to audio."""

from __future__ import annotations

import contextlib
import logging
import multiprocessing
import multiprocessing.queues
import sys
import time
import tkinter as tk
from dataclasses import dataclass
from enum import IntEnum
from queue import Empty
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from lightberries.array_controller import ArrayController
from lightberries.array_sequence.named import SequenceName, get_named_sequence
from lightberries.base.pixel import LEDOrder, Pixel
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

LOGGER = logging.getLogger("light_berry_sim")
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(logging.DEBUG)


class DataName(IntEnum):
    """Handy enum."""

    led_count = 0
    duration = 1
    delay = 2
    sequence = 3
    transform = 4
    command = 5


@dataclass
class SimConfig:
    """Handy data class."""

    name: DataName
    str_value: str = ""
    int_value: int = 0
    float_value: float = 0.0


class LightOutput:
    """Outputs audio FFT to light controller object."""

    def __init__(
        self,
        light_q: multiprocessing.Queue[SimConfig],
        plot_q: multiprocessing.Queue[NDArray[np.int32]],
        tk_q: multiprocessing.Queue[str | list[str]],
        exit_q: multiprocessing.Queue[str],
    ) -> None:
        """Output audio FFT to light controller object.

        Args:
        ----
            light_q: multiprocessing queue for receiving data
            plot_q: multiprocessing queue for sending data
            tk_q: multiprocessing queue for sending data
            exit_q: multiprocessing queue for sending data

        """
        self.light_q = light_q
        self.plot_q = plot_q
        self.tk_q = tk_q
        self.exit_q = exit_q
        self.delay: float = 0.1
        self.lightController: ArrayController
        self.has_run = False
        self.func = ""
        self.colr = ""
        # run routine
        self.run()

    def update(self) -> None:
        """Update the gui."""
        self.plot_q.put(self.lightController.virtual_led_buffer)
        if PixelTransform.ACTIVE_TRANSFORMS:
            if not isinstance(PixelTransform.ACTIVE_TRANSFORMS[0], TransformFadeOff):
                LOGGER.info(PixelTransform.ACTIVE_TRANSFORMS[0])
            else:
                LOGGER.info(PixelTransform.ACTIVE_TRANSFORMS[1])
        time.sleep(self.delay)

    def run(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Run the process."""
        try:
            led_count = 20
            while True:
                with contextlib.suppress(Empty):
                    msg = self.light_q.get_nowait()
                    if msg.name is DataName.led_count:
                        led_count = msg.int_value
                        self.lightController = ArrayController(
                            led_count=led_count,
                            pwm_gpio_pin=18,
                            dma_channel=10,
                            pwm_frequency=800000,
                            simulate=True,
                            refresh_callback=lambda: self.update(),
                            led_order=LEDOrder.RGB,
                        )
                        Pixel.order = LEDOrder.RGB
                        self.has_run = True
                    elif msg.name is DataName.duration:
                        self.lightController.seconds_per_mode = msg.float_value
                    elif msg.name is DataName.delay:
                        self.delay = msg.float_value
                    elif msg.name is DataName.sequence:
                        LOGGER.info(msg.str_value)
                        self.colr = msg.str_value
                    elif msg.name is DataName.transform:
                        LOGGER.info(msg.str_value)
                        self.func = msg.str_value
                    elif msg.name is DataName.command:
                        if msg.str_value == "go":
                            self.lightController.reset()
                            self.lightController.off()
                            self.lightController.refresh_leds()
                            if self.colr in PixelSequence.ALL_SEQUENCES:
                                sequence = PixelSequence.ALL_SEQUENCES[self.colr]()
                            else:
                                sequence = get_named_sequence(
                                    name=SequenceName[self.colr],
                                )
                            PixelTransform.ALL_TRANSFORMS[self.func].create(
                                controller=self.lightController,
                                pixel_sequence=sequence,
                            )
                            self.tk_q.put("running")
                            self.lightController.run(seconds_per_mode=self.lightController.seconds_per_mode)
                            self.tk_q.put("done")
                        elif msg.str_value == "quit":
                            break
        except KeyboardInterrupt:
            pass
        except Exception:
            LOGGER.exception("Error in %s", LightOutput.__name__)
        finally:
            # clean up the LightBerry object
            if self.has_run:
                self.lightController.off()
                self.lightController.copy_virtual_leds_to_ws281x()
                self.lightController.refresh_leds()
            # pause for object destruction
            time.sleep(0.2)
            # put any data in queue, this will signify "exit" status
            self.exit_q.put("quit")
            # double-check deletion
            if self.has_run:
                del self.lightController


class PlotOutput:
    """Plots audio FFT to matplotlib's pyplot graphic."""

    def __init__(
        self,
        plot_q: multiprocessing.Queue[NDArray[np.int32]],
        tk_q: multiprocessing.Queue[str | list[str]],
        exit_q: multiprocessing.Queue[str],
    ) -> None:
        """Plot audio FFT to matplotlib's pyplot graphic.

        Args:
        ----
            plot_q: multiprocessing queue for receiving data
            tk_q: multiprocessing queue for sending data
            exit_q: multiprocessing queue for sending data

        """
        self.plot_q = plot_q
        self.tk_q = tk_q
        self.exit_q = exit_q
        self.buttonCallback = None
        self.exiting = False
        plt.ion()  # type: ignore  # noqa: PGH003
        self.run()

    def run(self) -> None:
        """Run the process."""
        try:
            self.exiting = False
            while not self.exiting:
                msg = None
                array = None
                with contextlib.suppress(Empty):
                    # try to get new data
                    array = self.plot_q.get_nowait()
                with contextlib.suppress(Empty):
                    msg = self.exit_q.get_nowait()
                if array is not None:
                    self.tk_q.put([Pixel(rgb).hex_str for rgb in array])
                if msg is not None:
                    self.exiting = True
        except KeyboardInterrupt:
            pass
        except Exception:
            LOGGER.exception("Error in %s", PlotOutput.__name__)
        finally:
            self.exit_q.put("quit")


class App:
    """The application for tkinter."""

    def __init__(self) -> None:  # noqa: PLR0915
        """Application for tkinter."""
        # create tKinter GUI. This GUI could really use some help
        self.light_q: multiprocessing.Queue[SimConfig] = multiprocessing.Queue()
        self.plotQ: multiprocessing.Queue[NDArray[np.int32]] = multiprocessing.Queue()
        self.tk_q: multiprocessing.Queue[str | list[str]] = multiprocessing.Queue()
        self.exitQ: multiprocessing.Queue[str] = multiprocessing.Queue()
        # create process objects
        self.lightProcess = multiprocessing.Process(
            target=LightOutput,
            args=(
                self.light_q,
                self.plotQ,
                self.tk_q,
                self.exitQ,
            ),
        )
        self.guiProcess = multiprocessing.Process(
            target=PlotOutput,
            args=(
                self.plotQ,
                self.tk_q,
                self.exitQ,
            ),
        )
        # start the selected process
        self.lightProcess.start()
        self.guiProcess.start()

        self.ledCount = None
        self.buttons: list[tk.Button] = []
        self.running = False

        self.root = tk.Tk()

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side=tk.RIGHT, fill="both", expand=True)

        self.scrollbarY = tk.Scrollbar(
            self.canvas,
            command=self.canvas.yview,  # type: ignore  # noqa: PGH003
            orient=tk.VERTICAL,
        )
        self.scrollbarY.pack(side=tk.RIGHT, fill="y")
        self.scrollbarX = tk.Scrollbar(
            self.canvas,
            command=self.canvas.xview,  # type: ignore  # noqa: PGH003
            orient=tk.HORIZONTAL,
        )
        self.scrollbarX.pack(side=tk.BOTTOM, fill="y")

        self.mainFrame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.mainFrame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbarY.set)
        self.canvas.configure(xscrollcommand=self.scrollbarX.set)

        self.mainFrame.pack(fill="both", anchor=tk.NW, expand=True)
        self.mainFrame.rowconfigure(1, weight=1)
        self.mainFrame.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(1, weight=1)
        self.mainFrame.columnconfigure(2, weight=1)
        self.mainFrame.columnconfigure(3, weight=1)
        self.mainFrame.columnconfigure(4, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.destroy())

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
        self.ledCountInt.set(20)

        self.functionString = tk.StringVar()
        self.functionChoices = list(PixelTransform.ALL_TRANSFORMS)
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
        self.patternChoices = list(PixelSequence.ALL_SEQUENCES)
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
        self.delayFloat.set(0.01)
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
            command=self.configure_lightberries,
        )
        self.buttonGo.grid(
            row=0,
            column=8,
        )

        self.root.bind("<Return>", lambda _: self.configure_lightberries())

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

        self.root.title(
            "LightBerries LED GUI Simulator (function parameters not included)",
        )
        self.root.after(1, self.check_q)

        self.root.mainloop()

    def check_q(self) -> None:
        """Check whether other processes have sent us data."""
        self.root.after(1, self.check_q)
        try:
            data = self.tk_q.get_nowait()
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
        except Empty:
            pass

    def on_configure(self) -> None:
        """Configure the convas widget."""
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def configure_lightberries(self) -> None:
        """Configure LightBerries."""
        self.buttonFrame.children.clear()
        self.buttons.clear()
        led_count = int(self.ledCountInt.get())
        for column in range(led_count):
            self.buttonFrame.columnconfigure(column, weight=1)
            btn = tk.Button(
                self.buttonFrame,
                bg="black",
                fg="white",
                width=1,
                height=1,
            )
            btn.grid(
                row=1,
                column=column,
                sticky="nw",
            )
            self.buttons.append(btn)
        self.light_q.put_nowait(SimConfig(DataName.led_count, int_value=led_count))
        self.ledCount = led_count
        if self.running is False:
            self.light_q.put(SimConfig(name=DataName.duration, float_value=self.durationInt.get()))
            self.light_q.put(SimConfig(name=DataName.delay, float_value=self.delayFloat.get()))
            self.light_q.put(SimConfig(name=DataName.sequence, str_value=self.patternString.get()))
            self.light_q.put(SimConfig(name=DataName.transform, str_value=self.functionString.get()))
            self.light_q.put(SimConfig(name=DataName.command, str_value="go"))

    def destroy(self) -> None:
        """Destroy this object."""
        self.exitQ.put("quit")
        self.light_q.put(SimConfig(DataName.command, "quit"))
        self.root.destroy()
        self.__del__()

    def __del__(self) -> None:
        """Destroy the object cleanly."""


if __name__ == "__main__":
    app = App()
    del app
