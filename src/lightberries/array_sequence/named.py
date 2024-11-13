"""Create some named sequences."""

from enum import IntEnum, auto

from lightberries.array_sequence.transition import SequenceTransition
from lightberries.base.pixel import Pixel, PixelColor
from lightberries.pixel_sequence import PixelSequence


class SequenceName(IntEnum):
    """Named pixel sequences."""

    sunset = auto()


def get_named_sequence(name: SequenceName, led_count: int) -> PixelSequence:
    """Get a named sequence."""
    sequence: PixelSequence
    if name is SequenceName.sunset:
        sequence = SequenceTransition(
            name="SequenceSunset",
            led_count=led_count,
            pixel_sequence=[
                Pixel(PixelColor.ORANGE3),
                Pixel(PixelColor.RED),
                Pixel(PixelColor.MIDNIGHT),
                Pixel(PixelColor.MIDNIGHT),
                Pixel(PixelColor.RED),
                Pixel(PixelColor.ORANGE3),
                Pixel(PixelColor.SKY),
            ],
            wrap=True,
        )
    return sequence
