"""Basic function. It does nothing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:

    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState



class TransformNone(PixelTransform):
    """Basic function. It does nothing."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do nothing.

        Args:
        ----
            controller: array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformNone.__name__,
            controller=controller,
        )

    @staticmethod
    def setup(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        # create an object to put in the light data list so we don't just abort the run
        transform = TransformNone(controller=controller)
        if state is not None:
            transform.state = state
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        transform.ran_once = False
        TransformNone.ACTIVE_TRANSFORMS.append(transform)
        return TransformNone.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Do nothing."""
        if not self.ran_once:
            self.ran_once = True
            if self.state.pixel_sequence.led_count <= self.controller.virtual_led_count:
                self.controller.virtual_led_buffer[: self.state.pixel_sequence.led_count] = self.state.pixel_sequence
            else:
                self.controller.virtual_led_buffer[: self.controller.virtual_led_count] = self.state.pixel_sequence
