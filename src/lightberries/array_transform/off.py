"""Turn all Pixels OFF."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lightberries.pixel_transform import PixelTransform
from lightberries.transform_overlay._overlay_transform import OverlayTransform

if TYPE_CHECKING:

    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform
    from lightberries.state import TransformState



class TransformOff(OverlayTransform):
    """Turn all Pixels OFF."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Turn all Pixels OFF.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformOff.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        super().setup(
            color_sequence=color_sequence,
            state=state,
        )
        self.ACTIVE_TRANSFORMS.clear()
        self.ACTIVE_TRANSFORMS.append(self)
        return self.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Turn all Pixels OFF."""
        self.controller.virtual_led_buffer[:] *= 0
