"""Import all array sequences."""

from strenum import StrEnum

from lightberries.array_sequence.array_sequence import ArraySequence as ArraySequence
from lightberries.array_sequence.default import SequenceDefault as SequenceDefault
from lightberries.array_sequence.named import SequenceName
from lightberries.array_sequence.off import SequenceOff as SequenceOff
from lightberries.array_sequence.pseudo_random import (
    SequencePseudoRandom as SequencePseudoRandom,
)
from lightberries.array_sequence.rainbow import SequenceRainbow as SequenceRainbow
from lightberries.array_sequence.rainbow_repeating import (
    SequenceRainbowRepeating as SequenceRainbowRepeating,
)
from lightberries.array_sequence.random import SequenceRandom as SequenceRandom
from lightberries.array_sequence.reflect import SequenceReflect as SequenceReflect
from lightberries.array_sequence.repeat import SequenceRepeat as SequenceRepeat
from lightberries.array_sequence.solid import SequenceSolid as SequenceSolid
from lightberries.array_sequence.stretch import SequenceStretch as SequenceStretch
from lightberries.array_sequence.transition import (
    SequenceTransition as SequenceTransition,
)
from lightberries.pixel_sequence import PixelSequence

COLOR_SEQUENCE_NAMES = [name.lower() for name in PixelSequence.ALL_SEQUENCES] + [
    name.lower() for name in SequenceName._member_names_
]
ColorEnum = StrEnum("ColorEnum", COLOR_SEQUENCE_NAMES)
