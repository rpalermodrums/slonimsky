"""Slonimsky: an algorithmic reconstruction of the *Thesaurus of Scales and
Melodic Patterns* (1947), with tools to test it against the book."""

__version__ = "0.2.0"

from .cells import classify, parse_cell  # noqa: E402
from .progressions import PROGRESSIONS, get_progression  # noqa: E402
from .realize import realize  # noqa: E402
from .thesaurus import DEFAULT_RULES, Rules, build_chapter, build_thesaurus, locate  # noqa: E402

__all__ = [
    "__version__",
    "PROGRESSIONS",
    "DEFAULT_RULES",
    "Rules",
    "build_chapter",
    "build_thesaurus",
    "classify",
    "get_progression",
    "locate",
    "parse_cell",
    "realize",
]
