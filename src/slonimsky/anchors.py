"""Anchors: published facts about the book's numbering, and fitting them.

An anchor ties a book pattern number to a chapter and (usually) the pitch
classes of its cell. Most come from the twelve-tone rows Slonimsky's
patterns happen to form, as catalogued by Gotham & Yust's *Serial
Analyser* anthology; the rest are widely quoted facts. See
``data/anchors.csv`` for the sources, one per row.

``fit`` places every anchor in the canonical enumeration and scores each
section:

* **exact**: every anchor sits at the same offset (book number minus
  canonical index), so the enumeration reproduces the book's numbering and
  predicts the numbers of the patterns in between;
* **selection**: same order, but the book skips some of the enumeration;
* **reordered**: the book's order differs from the enumeration.

An anchor filed under a section whose pitch classes are *not* in that
section's enumeration is a **conflict** for it; a section with conflicts is
at best "mostly-exact" and makes no predictions.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from importlib import resources

from .progressions import PROGRESSIONS, Progression, get_progression
from .thesaurus import DEFAULT_RULES, Pattern, Rules, build_chapter, find_by_pcs, section_specs


@dataclass(frozen=True)
class Anchor:
    number: int
    progression: Progression
    label: str
    cell_pcs: tuple[int, ...] | None
    source: str
    note: str = ""
    offsets: tuple[int, ...] | None = None  # set when the source pins the register


    @property
    def section_key(self) -> str | None:
        return label_to_key(self.label, self.progression)


@dataclass
class Placement:
    anchor: Anchor
    pattern: Pattern | None
    relabelled: bool = False
    readings: int = 0  # how many register readings share these pitch classes


@dataclass
class SectionFit:
    progression: Progression
    key: str
    label: str
    size: int
    placements: list[Placement] = field(default_factory=list)
    conflicts: list[Anchor] = field(default_factory=list)
    verdict: str = "none"
    offset: int | None = None  # book number = offset + canonical index
    support: int = 0  # anchors agreeing with ``offset``

    def predicted_number(self, index: int) -> int | None:
        if self.offset is None:
            return None
        return self.offset + index


def _strip_label(label: str) -> str:
    label = label.strip()
    while label.startswith("["):
        close = label.find("]")
        if close < 0:
            break
        label = label[close + 1 :].strip()
    return label


def label_to_key(label: str, progression: Progression, rules: Rules = DEFAULT_RULES) -> str | None:
    wanted = _strip_label(label).lower()
    if not wanted:
        return None
    for spec in section_specs(progression, rules):
        if spec.label.lower() == wanted:
            return spec.key
    return None


def load_anchors(path: str | None = None) -> list[Anchor]:
    if path is None:
        text = resources.files("slonimsky").joinpath("data/anchors.csv").read_text("utf-8")
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    rows = csv.DictReader(line for line in text.splitlines() if not line.startswith("#"))
    anchors = []
    for row in rows:
        cell = row["cell"].strip()
        values = tuple(int(x) for x in cell.split()) if cell else None
        pcs = tuple(x % 12 for x in values) if values else None
        # signed values ("0 -1 +2 +9") give exact offsets, i.e. the register
        exact = values if values and ("+" in cell or "-" in cell) else None
        anchors.append(
            Anchor(
                number=int(row["number"]),
                progression=get_progression(row["progression"]),
                label=row["label"].strip(),
                cell_pcs=pcs,
                source=row["source"].strip(),
                note=(row.get("note") or "").strip(),
                offsets=exact,
            )
        )
    anchors.sort(key=lambda a: a.number)
    return anchors


def place(anchors: list[Anchor], rules: Rules = DEFAULT_RULES) -> list[Placement]:
    """Assign each anchor to one pattern of the canonical enumeration.

    Pitch classes can have several register readings, so prefer (1) the
    section the source labels it with, then (2) the earliest section not
    before the previous anchor's section (the book never goes back). Two
    anchors never share a pattern. Anchors filed under headings the
    reconstruction doesn't generate ("Miscellaneous Patterns", ...) stay
    unplaced.
    """
    out: list[Placement] = []
    for prog in PROGRESSIONS:
        order = {s.key: i for i, s in enumerate(section_specs(prog, rules))}
        claimed: set[str] = set()
        last_section = -1
        for a in (x for x in anchors if x.progression == prog):
            want = a.section_key
            if a.cell_pcs is None or (a.label and want is None):
                out.append(Placement(a, None))
                continue
            readings = find_by_pcs(prog, a.cell_pcs, rules)
            if a.offsets is not None:
                readings = [p for p in readings if p.cell == a.offsets]
            cands = [p for p in readings if p.id not in claimed]
            chosen, relabelled = None, False
            labelled = [p for p in cands if p.section.key == want]
            if labelled:
                chosen = labelled[0]
            else:
                later = [p for p in cands if order[p.section.key] >= last_section]
                if later:
                    chosen = later[0]
                    relabelled = want is not None
            if chosen is not None:
                claimed.add(chosen.id)
                last_section = max(last_section, order[chosen.section.key])
            out.append(Placement(a, chosen, relabelled, len(readings)))
    return out


def fit(anchors: list[Anchor] | None = None, rules: Rules = DEFAULT_RULES) -> list[SectionFit]:
    if anchors is None:
        anchors = load_anchors()
    placements = place(anchors, rules)
    fits: dict[tuple[str, str], SectionFit] = {}
    for prog in PROGRESSIONS:
        for section in build_chapter(prog, rules).sections:
            fits[(prog.key, section.spec.key)] = SectionFit(
                prog, section.spec.key, section.spec.label, len(section.patterns)
            )
    for pl in placements:
        if pl.pattern is not None:
            fits[(pl.pattern.progression.key, pl.pattern.section.key)].placements.append(pl)
            continue
        a = pl.anchor
        if a.cell_pcs is not None and (a.progression.key, a.section_key) in fits:
            fits[(a.progression.key, a.section_key)].conflicts.append(a)
    result = []
    for sf in fits.values():
        if not sf.placements:
            continue
        sf.placements.sort(key=lambda p: p.anchor.number)
        offsets = [p.anchor.number - p.pattern.index for p in sf.placements]
        offset, support = Counter(offsets).most_common(1)[0]
        sf.offset, sf.support = offset, support
        n = len(sf.placements)
        idx = [p.pattern.index for p in sf.placements]
        nums = [p.anchor.number for p in sf.placements]
        in_order = all(b > a for a, b in zip(idx, idx[1:]))
        subset = in_order and all(
            (nb - na) <= (ib - ia) for na, nb, ia, ib in zip(nums, nums[1:], idx, idx[1:])
        )
        if n == 1:
            sf.verdict = "single"
        elif support == n and not sf.conflicts:
            sf.verdict = "exact"
        elif subset and support < n:
            sf.verdict = "selection"
        elif support >= 2 and 2 * support >= n:
            sf.verdict = "mostly-exact"
        else:
            sf.verdict = "reordered"
        if sf.verdict not in ("exact", "mostly-exact", "single"):
            sf.offset = None
        result.append(sf)
    order = {p.key: p.order for p in PROGRESSIONS}
    result.sort(key=lambda s: (order[s.progression.key], s.placements[0].anchor.number))
    return result


def fit_summary(fits: list[SectionFit]) -> dict:
    multi = [f for f in fits if len(f.placements) >= 2]
    return {
        "sections": len(fits),
        "anchorsPlaced": sum(len(f.placements) for f in fits),
        "verdicts": dict(Counter(f.verdict for f in fits)),
        "multiAnchorSections": len(multi),
        "multiAnchorInOrder": sum(1 for f in multi if _in_order(f)),
        "conflicts": sum(len(f.conflicts) for f in fits),
        "anchorsReproducedExactly": sum(len(f.placements) for f in multi if f.verdict == "exact"),
        "predictedNumbers": sum(f.size for f in multi if f.verdict == "exact"),
    }


def _in_order(f: SectionFit) -> bool:
    idx = [p.pattern.index for p in f.placements]
    return all(b > a for a, b in zip(idx, idx[1:]))


def predictions(fits: list[SectionFit], min_support: int = 2) -> dict[str, dict]:
    """Book numbers implied by exactly-fitting sections: pattern id -> info."""
    out: dict[str, dict] = {}
    for f in fits:
        if f.verdict != "exact" or f.support < min_support:
            continue
        chapter = build_chapter(f.progression)
        section = next(s for s in chapter.sections if s.spec.key == f.key)
        confirmed = {pl.pattern.id: pl.anchor.number for pl in f.placements}
        for p in section.patterns:
            num = f.offset + p.index
            status = "confirmed" if confirmed.get(p.id) == num else "predicted"
            out[p.id] = {"number": num, "status": status}
    return out
