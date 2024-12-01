"""Overlay transform that doesn't permanently modify anything."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    from lightberries.array_controller import ArrayController


class OverlayTransform(PixelTransform):
    """Overlay transform that doesn't permanently modify anything."""

    ALL_OVERLAY_TRANSFORMS: ClassVar[dict[str, type[OverlayTransform]]] = {}

    def __init_subclass__(cls, **kwargs) -> None:  # type: ignore  # noqa: ANN003, PGH003
        OverlayTransform.ALL_OVERLAY_TRANSFORMS[cls.__name__] = cls
        return super().__init_subclass__(kwargs=kwargs)

    def __init__(
        self,
        name: str,
        controller: ArrayController,
    ) -> None:
        """Overlay transform that doesn't permanently modify anything.

        Args:
        ----
            name: name of transform
            controller: Array controller instance
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        """
        super().__init__(
            name=name,
            controller=controller,
        )
