"""Generative reconstruction of the Thesaurus' progression chapters.

The rules below are the ones the published numbering supports (see
docs/FINDINGS.md for the evidence and where they break down):

1. A chapter is an equal division of N octaves into M parts (principal
   interval P). Chapters run in book order.
2. Inside a chapter, sections run: Interpolation (1..k notes),
   Ultrapolation (1..k), Infrapolation (1..k), then the mixed forms
   Infra-Inter, Inter-Ultra, Infra-Ultra, Infra-Inter-Ultra and
   Inter-Infra-Ultra.
3. Each role draws from a window of candidate notes, ordered from the
   nearest principal tone outwards:
     * interpolation: every note strictly between the principal tones;
     * infra/ultrapolation, single-role sections: up to an octave span,
       i.e. ``max(11 - P, 3)`` semitones beyond the principal tone;
     * infra/ultrapolation in mixed sections: ultrapolations reach one
       semitone past the principal tone after next (``P + 1``),
       infrapolations one semitone further (``P + 2``), both capped by
       the single-role window.
4. Cells are enumerated lexicographically, earlier notes varying slowest.
5. A cell may not repeat a pitch class (counting the next principal tone).
6. Multi-note infra/ultrapolations move monotonically: infrapolations
   step further down, ultrapolations descend onto the next principal
   tone. Slonimsky's own selection also uses zig-zag orders, available
   with ``contour="any"`` (every ordering, grouped by melodic shape).

Rules 3-5 reproduce the book's numbering exactly wherever a section is
small enough to be listed in full. In every larger section with enough
anchors to check, the book's patterns appear in this enumeration's order,
with some skipped: the book is a *selection* from this space.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from functools import lru_cache
from itertools import combinations, permutations, product

from .cells import INFRA, INTER, ULTRA, Cell, has_pc_repeat, roles_of, section_key, section_label
from .progressions import PROGRESSIONS, Progression, get_progression

MIXED_SECTIONS: tuple[tuple[str, ...], ...] = (
    (INFRA, INTER),
    (INTER, ULTRA),
    (INFRA, ULTRA),
    (INFRA, INTER, ULTRA),
    (INTER, INFRA, ULTRA),
)


@dataclass(frozen=True)
class Rules:
    max_notes: int = 3
    min_window: int = 3
    mixed_infra_reach: int = 2  # mixed-section infra window = P + this
    mixed_ultra_reach: int = 1  # mixed-section ultra window = P + this
    forbid_pc_repeats: bool = True
    contour: str = "monotone"  # or "any"
    mixed: tuple[tuple[str, ...], ...] = field(default=MIXED_SECTIONS)

    def single_window(self, interval: int) -> int:
        return max(11 - interval, self.min_window)

    def mixed_window(self, interval: int, role: str) -> int:
        reach = self.mixed_infra_reach if role == INFRA else self.mixed_ultra_reach
        return min(interval + reach, self.single_window(interval))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["mixed"] = ["".join(m) for m in self.mixed]
        return d


DEFAULT_RULES = Rules()


@dataclass(frozen=True)
class SectionSpec:
    roles: tuple[str, ...]

    @property
    def key(self) -> str:
        return section_key(self.roles)

    @property
    def label(self) -> str:
        return section_label(self.roles)

    @property
    def mixed(self) -> bool:
        return len(set(self.roles)) > 1


@dataclass(frozen=True)
class Pattern:
    progression: Progression
    section: SectionSpec
    index: int  # 1-based position inside its section
    cell: Cell

    @property
    def id(self) -> str:
        return pattern_id(self.progression, self.cell)


@dataclass(frozen=True)
class Section:
    spec: SectionSpec
    patterns: tuple[Pattern, ...]


@dataclass(frozen=True)
class Chapter:
    progression: Progression
    sections: tuple[Section, ...]

    def patterns(self) -> list[Pattern]:
        return [p for s in self.sections for p in s.patterns]


def pattern_id(progression: Progression, cell: Cell) -> str:
    return f"{progression.key}:{','.join(str(x) for x in cell[1:])}"


def parse_pattern_id(pid: str) -> tuple[Progression, Cell]:
    key, _, rest = pid.partition(":")
    cell = (0,) + tuple(int(x) for x in rest.split(",") if x)
    return get_progression(key), cell


def window(interval: int, role: str, width: int) -> list[int]:
    """Candidate offsets for a role, nearest principal tone first."""
    if role == INTER:
        return list(range(1, interval))
    if role == INFRA:
        return [-d for d in range(1, width + 1)]
    if role == ULTRA:
        return [interval + d for d in range(1, width + 1)]
    raise ValueError(role)


def section_specs(progression: Progression, rules: Rules = DEFAULT_RULES) -> list[SectionSpec]:
    specs = []
    for role in (INTER, ULTRA, INFRA):
        for n in range(1, rules.max_notes + 1):
            specs.append(SectionSpec((role,) * n))
    specs.extend(SectionSpec(m) for m in rules.mixed)
    return specs


def _single_role_tuples(interval: int, role: str, n: int, rules: Rules) -> list[tuple[int, ...]]:
    width = rules.single_window(interval)
    cand = window(interval, role, width)
    if role == INTER:
        return list(combinations(cand, n))  # ascending through the interval
    if rules.contour == "any":
        # Every ordering of every note choice, grouped by melodic shape first
        # (the only ordering consistent with the book's zig-zag ultrapolations).
        rank = {x: i for i, x in enumerate(cand)}
        out = [p for c in combinations(cand, n) for p in permutations(c)]
        out.sort(key=lambda t: (_shape(tuple(rank[x] for x in t)), tuple(rank[x] for x in t)))
        return out
    if role == INFRA:
        return list(combinations(cand, n))  # -1, -2, ...: stepping further down
    # ULTRA: start furthest from the target, descend onto it.
    rank = {x: i for i, x in enumerate(cand)}
    out = [tuple(reversed(c)) for c in combinations(cand, n)]
    out.sort(key=lambda t: tuple(rank[x] for x in t))
    return out


def _shape(ranks: tuple[int, ...]) -> tuple[int, ...]:
    """Relative order of the notes' distances: (0, 2, 1) = near, far, middle."""
    ordered = sorted(ranks)
    return tuple(ordered.index(r) for r in ranks)


def _mixed_tuples(interval: int, roles: tuple[str, ...], rules: Rules) -> list[tuple[int, ...]]:
    return list(product(*(window(interval, r, rules.mixed_window(interval, r)) for r in roles)))


@lru_cache(maxsize=None)
def enumerate_section(
    progression: Progression, spec: SectionSpec, rules: Rules = DEFAULT_RULES
) -> tuple[Cell, ...]:
    P = progression.interval
    roles = spec.roles
    if spec.mixed:
        tuples = _mixed_tuples(P, roles, rules)
    else:
        tuples = _single_role_tuples(P, roles[0], len(roles), rules)
    cells = []
    for t in tuples:
        cell = (0,) + tuple(t)
        if rules.forbid_pc_repeats and has_pc_repeat(cell, P):
            continue
        cells.append(cell)
    return tuple(cells)


@lru_cache(maxsize=None)
def build_chapter(progression: Progression, rules: Rules = DEFAULT_RULES) -> Chapter:
    sections = []
    for spec in section_specs(progression, rules):
        cells = enumerate_section(progression, spec, rules)
        if not cells:
            continue
        patterns = tuple(Pattern(progression, spec, i + 1, c) for i, c in enumerate(cells))
        sections.append(Section(spec, patterns))
    return Chapter(progression, tuple(sections))


def build_thesaurus(rules: Rules = DEFAULT_RULES) -> list[Chapter]:
    return [build_chapter(p, rules) for p in PROGRESSIONS]


def locate(progression: Progression, cell: Cell, rules: Rules = DEFAULT_RULES) -> Pattern | None:
    """Find a cell in the canonical enumeration (None if outside it)."""
    roles = roles_of(cell, progression.interval)
    spec = SectionSpec(roles)
    cells = enumerate_section(progression, spec, rules)
    try:
        i = cells.index(tuple(cell))
    except ValueError:
        return None
    return Pattern(progression, spec, i + 1, tuple(cell))


def find_by_pcs(
    progression: Progression, pcs: tuple[int, ...], rules: Rules = DEFAULT_RULES
) -> list[Pattern]:
    """All canonical patterns whose cell has these pitch classes, in order.

    Pitch classes alone don't fix register: ``C B`` in the whole-tone
    chapter is both an ultrapolation (B above D) and an infrapolation
    (B below C). Every reading in the enumeration is returned.
    """
    want = tuple(x % 12 for x in pcs)
    out = []
    for section in build_chapter(progression, rules).sections:
        for p in section.patterns:
            if tuple(x % 12 for x in p.cell) == want:
                out.append(p)
    return out
