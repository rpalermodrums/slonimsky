"""Build the JSON catalog the web UI (and anyone else) reads."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from . import __version__
from .analysis import analyze
from .anchors import SectionFit, fit, fit_summary, load_anchors, place, predictions
from .cells import describe
from .progressions import PROGRESSIONS
from .thesaurus import DEFAULT_RULES, Rules, build_chapter, pattern_id


def _fit_json(fits: list[SectionFit]) -> list[dict]:
    out = []
    for f in fits:
        out.append({
            "progression": f.progression.key,
            "section": f.key,
            "label": f.label,
            "size": f.size,
            "verdict": f.verdict,
            "offset": f.offset,
            "support": f.support,
            "anchors": [
                {
                    "number": p.anchor.number,
                    "id": p.pattern.id,
                    "index": p.pattern.index,
                    "cell": list(p.pattern.cell),
                    "relabelled": p.relabelled,
                }
                for p in f.placements
            ],
            "conflicts": [{"number": a.number, "cell": list(a.cell_pcs)} for a in f.conflicts],
        })
    return out


def build_catalog(rules: Rules = DEFAULT_RULES) -> dict:
    anchors = load_anchors()
    fits = fit(anchors, rules)
    predicted = predictions(fits)
    placements = {pl.anchor.number: pl for pl in place(anchors, rules)}
    confirmed = {pl.pattern.id: pl.anchor.number for pl in placements.values() if pl.pattern}

    progressions = []
    for prog in PROGRESSIONS:
        chapter = build_chapter(prog, rules)
        sections = []
        for section in chapter.sections:
            patterns = []
            for p in section.patterns:
                a = analyze(prog, p.cell)
                item = {
                    "id": p.id,
                    "i": p.index,
                    "cell": list(p.cell),
                    "scale": a["scale"],
                    "card": a["cardinality"],
                    "sym": a["transpositions"],
                    "row": a["twelveTone"],
                }
                if p.id in predicted:
                    item["book"] = predicted[p.id]
                elif p.id in confirmed:
                    item["book"] = {"number": confirmed[p.id], "status": "confirmed"}
                patterns.append(item)
            sections.append({
                "key": section.spec.key,
                "label": section.spec.label,
                "roles": list(section.spec.roles),
                "patterns": patterns,
            })
        d = prog.to_dict()
        d["sections"] = sections
        d["count"] = sum(len(s["patterns"]) for s in sections)
        progressions.append(d)

    anchor_rows = []
    for a in anchors:
        pl = placements.get(a.number)
        row = {
            "number": a.number,
            "progression": a.progression.key,
            "label": a.label,
            "cell": list(a.cell_pcs) if a.cell_pcs is not None else None,
            "source": a.source,
            "note": a.note,
            "placed": None,
        }
        if pl and pl.pattern:
            row["placed"] = {
                "id": pl.pattern.id,
                "section": pl.pattern.section.key,
                "index": pl.pattern.index,
                "cell": list(pl.pattern.cell),
                "relabelled": pl.relabelled,
                "readings": pl.readings,
            }
        anchor_rows.append(row)

    any_rules = Rules(**{**rules.__dict__, "contour": "any"})
    any_fits = fit(anchors, any_rules)

    return {
        "version": __version__,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rules": rules.to_dict(),
        "windows": {
            p.key: {
                "inter": p.interval - 1,
                "single": rules.single_window(p.interval),
                "mixedInfra": rules.mixed_window(p.interval, "I"),
                "mixedUltra": rules.mixed_window(p.interval, "U"),
            }
            for p in PROGRESSIONS
        },
        "progressions": progressions,
        "anchors": anchor_rows,
        "fit": _fit_json(fits),
        "fitSummary": fit_summary(fits),
        "fitAnyContour": _fit_json(any_fits),
        "fitAnyContourSummary": fit_summary(any_fits),
        "total": sum(p["count"] for p in progressions),
    }


def pattern_detail(progression, cell, rules: Rules = DEFAULT_RULES) -> dict:
    """Everything the CLI's `show` prints, as data."""
    from .thesaurus import locate

    loc = locate(progression, cell, rules)
    return {
        "id": pattern_id(progression, cell),
        "progression": progression.key,
        "cell": list(cell),
        "derivation": describe(cell, progression.interval),
        "section": loc.section.label if loc else None,
        "index": loc.index if loc else None,
        "analysis": analyze(progression, cell),
    }


def dumps(catalog: dict, compact: bool = True) -> str:
    if compact:
        return json.dumps(catalog, separators=(",", ":"), ensure_ascii=False)
    return json.dumps(catalog, indent=2, ensure_ascii=False)
