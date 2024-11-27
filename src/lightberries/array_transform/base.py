"""Functions that modify the LED patterns in interesting ways."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller


class ArrayTransform(PixelTransform):
    """Modify LED patterns in interesting ways."""

    ALL_ARRAY_TRANSFORMS: ClassVar[dict[str, type[ArrayTransform]]] = {}

    def __init_subclass__(
        cls,
        **kwargs: dict[str, Any],
    ) -> None:
        super().__init_subclass__(kwargs=kwargs)
        cls_name = cls.__name__.replace("Transform", "")
        if cls_name not in (
            "Overlay",
            "Array",
            "Off",
            "FadeOff",
            "CollisionDetect",
            "None",
            "Fade",
            "Blink",
            "Twinkle",
        ):
            cls.ALL_ARRAY_TRANSFORMS[cls_name] = cls

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        name: str | None = None,
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
        ----
            name: name of the function
            controller: Array controller instance
            pixel_sequence: a sequence of pixels
            state: initial state. Defaults to None.

        """
        if name is None:
            name = ArrayTransform.__name__
        super().__init__(
            name=name,
            controller=controller,
        )
