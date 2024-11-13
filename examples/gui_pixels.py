#!/usr/bin/python3
"""Example of using LightBerries module functions with a GUI.

Use GUI to interact with individual LEDs.
"""
from __future__ import annotations

import contextlib
import logging
import multiprocessing
import multiprocessing.queues
import queue
import time
import tkinter as tk
from multiprocessing import Queue
from tkinter.colorchooser import askcolor
from typing import TYPE_CHECKING, Any

import lightberries.base.pixel
from lightberries.array_controller import ArrayController
from lightberries.array_sequence.solid import SequenceSolid
from lightberries.base.pixel import Pixel

if TYPE_CHECKING:

    import numpy as np
    from numpy.typing import NDArray

LOGGER = logging.getLogger("pixel_gui")

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
Pixel.default_pixel_order = lightberries.base.pixel.LEDOrder.RGB.value


class LedButton(tk.Button):
    """Custom type wrapper that knows about my custom index."""

    def __init__(  # noqa: D107
        self,
        master=None,  # noqa: ANN001, PGH003, RUF100 # type: ignore
        cnf={},  # noqa: ANN001, B006, PGH003, RUF100 # type: ignore
        **kwargs: dict[str, Any],
    ) -> None:
        super().__init__(master=master, cnf=cnf, **kwargs)  # type: ignore  # noqa: PGH003
        self.led_index: int | None = 0


class LightsProcess:
    """Handles LightBerries functions in a separate process."""

    self_object = None
    app_object = None

    def __init__(self, app: App) -> None:
        """Handle LightBerries functions in a separate process.

        Args:
        ----
            app: the tkinter app

        """
        LightsProcess.self_object = self
        LightsProcess.app_object = app
        self.in_q: Queue[tuple[str, int, int]] = Queue(2)
        self.out_q: Queue[tuple[int, NDArray[np.int32]]] = Queue(2)
        self.process = multiprocessing.Process(target=LightsProcess.main_loop, args=[self.in_q, self.out_q])
        self.process.start()

    def __del__(self) -> None:
        """Clean up memory."""
        self.process.terminate()

    @classmethod
    def main_loop(cls, in_q: Queue[tuple[str, int, int]], _: Any) -> None:  # noqa: ANN401
        """Loop happens.

        Args:
        ----
            in_q: multiprocess queue for getting input
            _ : [description]

        """
        light_control = None
        try:
            # create LightBerry controller
            light_control = ArrayController(
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
        except KeyboardInterrupt:
            pass
        except Exception:
            LOGGER.exception("whoops")
        if light_control is not None:
            try:
                light_control.set_virtual_led_buffer(
                    SequenceSolid(
                        led_count=PIXEL_COUNT,
                        color=lightberries.base.pixel.PixelColor.OFF,
                    ),
                )
                light_control.copy_virtual_leds_to_ws281x()
                light_control.refresh_leds()

                # run loop forever
                while True:
                    # check for new user input
                    msg = None
                    with contextlib.suppress(Exception):
                        msg = in_q.get()
                    if msg is not None:
                        LOGGER.critical(msg)
                        if msg[0] == "color":
                            try:
                                index, color = msg[1:]
                                LOGGER.critical("setting color")
                                Pixel.default_pixel_order = lightberries.base.pixel.LEDOrder.RGB.value
                                light_control.virtual_led_buffer[index] = Pixel(
                                    color,
                                ).array
                                light_control.copy_virtual_leds_to_ws281x()
                                light_control.refresh_leds()
                                time.sleep(0.05)
                            except Exception:
                                LOGGER.exception("oh no")
                    time.sleep(0.001)
            except KeyboardInterrupt:
                pass
            except Exception:
                LOGGER.exception("aaah")
            light_control.__del__()
            time.sleep(0.05)


class App:
    """The application for tkinter."""

    def __init__(self) -> None:
        """Application for tkinter."""
        # create tKinter GUI. This GUI could really use some help
        self.root = tk.Tk()

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side=tk.RIGHT, fill="both", expand=True)

        self.scrollbarY = tk.Scrollbar(self.canvas, command=self.canvas.yview, orient=tk.VERTICAL)  # type: ignore  # noqa: PGH003
        self.scrollbarY.pack(side=tk.RIGHT, fill="y")
        self.scrollbarX = tk.Scrollbar(self.canvas, command=self.canvas.xview, orient=tk.HORIZONTAL)  # type: ignore  # noqa: PGH003
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
        self.canvas.bind("<Configure>", lambda _: self.on_configure())

        self.columnInt = tk.IntVar(value=3)
        self.columnString = tk.StringVar()

        self.columnLabel = tk.Label(
            self.mainFrame,
            text="LED Count",
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

        self.configureButton = LedButton(
            self.mainFrame,
            text="Configure",  # type: ignore  # noqa: PGH003
            command=self.configure_lightberries,  # type: ignore  # noqa: PGH003
        )
        self.configureButton.grid(
            row=0,
            column=4,
            sticky="news",
        )
        self.root.bind("<Return>", lambda _: self.configure_lightberries())

        self.leftClickColorBtn = LedButton(
            self.mainFrame,
            bg="black",  # type: ignore  # noqa: PGH003
            fg="white",  # type: ignore  # noqa: PGH003
            text="Left-Click\nColor",  # type: ignore  # noqa: PGH003
            width=5,  # type: ignore  # noqa: PGH003
            height=2,  # type: ignore  # noqa: PGH003
        )
        self.leftClickColorBtn.grid(
            row=0,
            column=5,
            sticky="news",
        )
        self.leftClickColorBtn.led_index = None  # type: ignore  # noqa: PGH003
        self.leftClickColorBtn.bind("<Button-1>", self.get_color)  # type: ignore  # noqa: PGH003

        self.rightClickColorBtn = LedButton(
            self.mainFrame,
            bg="black",  # type: ignore  # noqa: PGH003
            fg="white",  # type: ignore  # noqa: PGH003
            text="Right-Click\nColor",  # type: ignore  # noqa: PGH003
            width=5,  # type: ignore  # noqa: PGH003
            height=2,  # type: ignore  # noqa: PGH003
        )
        self.rightClickColorBtn.grid(
            row=0,
            column=6,
            sticky="news",
        )
        self.rightClickColorBtn.led_index = None  # type: ignore  # noqa: PGH003
        self.rightClickColorBtn.bind("<Button-1>", self.get_color)  # type: ignore  # noqa: PGH003
        self.rightClickColorBtn.bind("<Button-3>", self.get_color)  # type: ignore  # noqa: PGH003

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

    def on_configure(self) -> None:
        """Configure the canvas widget."""
        # update scroll region after starting 'mainloop'
        # when all widgets are in canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def configure_lightberries(self) -> None:
        """Configure LightBerries."""
        counter = 0
        try:
            for row in range(1):
                self.buttonFrame.rowconfigure(row, weight=1)
                for column in range(int(self.columnString.get())):
                    self.buttonFrame.columnconfigure(column, weight=1)
                    btn = LedButton(
                        self.buttonFrame,
                        bg="black",  # type: ignore  # noqa: PGH003
                        fg="white",  # type: ignore  # noqa: PGH003
                        text=str(counter),  # type: ignore  # noqa: PGH003
                        width=5,  # type: ignore  # noqa: PGH003
                        height=2,  # type: ignore  # noqa: PGH003
                    )
                    btn.grid(
                        row=row,
                        column=column,
                        sticky="nw",
                    )
                    btn.bind("<Button-1>", self.get_color)
                    btn.bind("<Button-3>", self.get_color2)  # type: ignore  # noqa: PGH003
                    btn.grid(column=column, row=row, sticky="nw")
                    btn.led_index = counter
                    counter += 1
            self.configureButton["state"] = "disabled"
        except Exception:
            LOGGER.exception("another one")

    def destroy(self) -> None:
        """Destroy this object."""
        self.root.destroy()
        self.__del__()

    def get_color(self, event: tk.Event[LedButton]) -> None:
        """Get a color from user, pass it to LightBerries.

        Args:
        ----
            event: tkinter widget event object

        """
        if event.widget.led_index is None:
            color = askcolor(event.widget["background"])
            if color[0] is not None:
                rgb = color[0]
                color_int = int(rgb[0] << 16 + rgb[1] << 8 + rgb[2])
                color_hex = str(color[1])
                event.widget.configure(background=color_hex)
                event.widget.configure(activebackground=color_hex)
                invert_color = 0xFFFFFF - color_int
                invert_color_hex = "#" + f"{invert_color:06X}"[-6:]
                event.widget.configure(foreground=invert_color_hex)
        else:
            color = self.leftClickColorBtn["background"]
            event.widget.configure(background=color)
            event.widget.configure(activebackground=color)
            invert_color = self.leftClickColorBtn["foreground"]
            event.widget.configure(foreground=invert_color)
            try:
                color = int(color[1:], 16)
                self.lights.in_q.put_nowait(("color", event.widget.led_index, color))
            except queue.Full:
                pass

    def get_color2(self, event: tk.Event[Any]) -> None:
        """Get a color from user, pass it to LightBerries.

        Args:
        ----
            event: tkinter widget event object

        """
        color = self.rightClickColorBtn["background"]
        event.widget.configure(bg=color)
        invert_color = self.rightClickColorBtn["foreground"]
        event.widget.configure(fg=invert_color)
        try:
            color = int(color[1:], 16)
            self.lights.in_q.put_nowait(("color", event.widget.led_index, color))
        except queue.Full:
            pass

    def __del__(self) -> None:
        """Destroy the object cleanly."""
        del self.lights


if __name__ == "__main__":
    the_app = App()
    del the_app
