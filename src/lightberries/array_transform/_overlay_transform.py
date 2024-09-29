"""Overlay transform that doesn't permanently modify anything."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from lightberries.pixel_transform import PixelTransform, TransformState

if TYPE_CHECKING:
    from lightberries.array_controller import ArrayController


class OverlayTransform(PixelTransform):
    """Overlay transform that doesn't permanently modify anything."""

    ALL_OVERLAY_TRANSFORMS: ClassVar[dict[str, type[OverlayTransform]]] = {}

    def __init_subclass__(cls, **kwargs) -> None:  # type: ignore  # noqa: ANN003, PGH003
        super().__init_subclass__(kwargs=kwargs)
        cls_name = cls.__name__.replace("Transform", "")
        if cls_name not in ("Overlay", "Array", "Off", "FadeOff", "CollisionDetect", "None", "Fade"):
            OverlayTransform.ALL_OVERLAY_TRANSFORMS[cls_name] = cls

    def __init__(
        self,
        name: str,
        controller: ArrayController,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],
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
            state=state,
            kwargs=kwargs,
        )
