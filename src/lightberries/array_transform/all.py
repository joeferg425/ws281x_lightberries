"""Light array functions."""

from strenum import StrEnum

from lightberries.array_transform.accelerate import (
    TransformAccelerate as TransformAccelerate,
)
from lightberries.array_transform.alive import TransformAlive as TransformAlive
from lightberries.array_transform.cycle import TransformCycle as TransformCycle
from lightberries.array_transform.cylon import TransformCylon as TransformCylon
from lightberries.array_transform.marquee import TransformMarquee as TransformMarquee
from lightberries.array_transform.merge import TransformMerge as TransformMerge
from lightberries.array_transform.meteors import TransformMeteor as TransformMeteor
from lightberries.array_transform.none import TransformNone as TransformNone
from lightberries.array_transform.raindrops import (
    TransformRaindrop as TransformRaindrop,
)
from lightberries.array_transform.random import TransformRandom as TransformRandom
from lightberries.array_transform.shift import TransformShift as TransformShift
from lightberries.array_transform.sprite import TransformSprite as TransformSprite
from lightberries.overlay.fade import TransformFade as TransformFade
from lightberries.pixel_transform import PixelTransform

FUNCTION_NAMES = [name.lower() for name in PixelTransform.ALL_TRANSFORMS]
FunctionEnum = StrEnum("FunctionEnum", FUNCTION_NAMES)
