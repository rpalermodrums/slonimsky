"""Command-line interface: ``slonimsky <command>`` (or ``python -m slonimsky``)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analysis import analyze
from .anchors import fit, fit_summary, load_anchors
from .cells import CellError, classify, describe, parse_cell
from .notation import to_abc
from .pitch import midi_name, parse_midi, parse_pc, pc_name
from .progressions import PROGRESSIONS, Progression, get_progression
from .realize import realize, spelling_sharps
from .thesaurus import (
    DEFAULT_RULES,
    Rules,
    build_chapter,
    enumerate_section,
    find_by_pcs,
    locate,
    parse_pattern_id,
)

ROLE_NAME = {"P": "principal", "I": "infra", "N": "inter", "U": "ultra"}


def _rules(args) -> Rules:
    kw = {}
    if getattr(args, "contour", None):
        kw["contour"] = args.contour
    if getattr(args, "max_notes", None):
        kw["max_notes"] = args.max_notes
    return Rules(**kw) if kw else DEFAULT_RULES


def _spell_cell(prog: Progression, cell, sharps: bool) -> str:
    names = [pc_name(x, sharps) for x in cell]
    return " ".join(names) + " -> " + pc_name(prog.interval, sharps)


def _resolve(args) -> tuple[Progression, tuple[int, ...]]:
    """Accept 'ditone:-1,2,9' or '<progression> <offsets...>'."""
    target = args.pattern
    if ":" in target[0]:
        return parse_pattern_id(target[0])
    prog = get_progression(target[0])
    return prog, parse_cell(" ".join(target[1:]))


def cmd_chapters(args) -> int:
    rules = _rules(args)
    for p in PROGRESSIONS:
        ch = build_chapter(p, rules)
        n = sum(len(s.patterns) for s in ch.sections)
        rng = f"#{p.book_range[0]}-{p.book_range[1]}" if p.book_range else ""
        print(f"{p.order:2d}. {p.title:28s} P={p.interval:2d}  {p.description:52s} {n:4d} patterns  {rng}")
    return 0


def cmd_sections(args) -> int:
    prog = get_progression(args.progression)
    for s in build_chapter(prog, _rules(args)).sections:
        print(f"{s.spec.key:22s} {s.spec.label:38s} {len(s.patterns):4d}")
    return 0


def cmd_list(args) -> int:
    rules = _rules(args)
    prog = get_progression(args.progression)
    sharps = spelling_sharps(prog, args.spelling)
    for s in build_chapter(prog, rules).sections:
        if args.section and s.spec.key != args.section:
            continue
        print(f"== {s.spec.label} ({len(s.patterns)})")
        for p in s.patterns[: args.limit or None]:
            a = analyze(prog, p.cell)
            tags = [t for t in (a["scale"], "12-tone row" if a["twelveTone"] else None) if t]
            extra = f"  [{', '.join(tags)}]" if tags else ""
            print(f"  {p.index:3d}. {_spell_cell(prog, p.cell, sharps):28s} {p.id}{extra}")
    return 0


def cmd_show(args) -> int:
    rules = _rules(args)
    prog, cell = _resolve(args)
    sharps = spelling_sharps(prog, args.spelling)
    c = classify(cell, prog.interval)
    loc = locate(prog, cell, rules)
    print(f"{prog.title}: {prog.description}")
    print(f"Section: {c.label}" + (f", #{loc.index} in the canonical enumeration" if loc else
                                  " (outside the canonical enumeration)"))
    print("Cell:")
    for d in describe(cell, prog.interval):
        print(f"  {pc_name(d['offset'], sharps):3s} {d['offset']:+4d}  {ROLE_NAME.get(d['role'], d['role']):9s} {d['text']}")
    root = parse_midi(args.root)
    notes = realize(prog, cell, root, args.direction)
    print("Notes:", " ".join(midi_name(n.midi, sharps) for n in notes))
    a = analyze(prog, cell)
    print(f"Pitch-class set: {a['pcs']}  prime form {a['primeForm']}  interval vector {a['intervalVector']}")
    if a["scale"]:
        print(f"Collection: {a['scale']}")
    print(f"Distinct transpositions: {a['transpositions']}   twelve-tone row: {a['twelveTone']}")
    if args.abc:
        print()
        print(to_abc(notes, title=f"{prog.name}: {c.label}", sharps=sharps))
    return 0


def cmd_classify(args) -> int:
    rules = _rules(args)
    prog = get_progression(args.progression)
    tokens = args.notes
    sharps = spelling_sharps(prog, args.spelling)
    if all(t.lstrip("+-").isdigit() for t in tokens):
        cells = [parse_cell(" ".join(tokens))]
    elif all(any(ch.isdigit() for ch in t) for t in tokens):
        midis = [parse_midi(t) for t in tokens]
        cells = [tuple(m - midis[0] for m in midis)]
    else:
        pcs = [(parse_pc(t) - parse_pc(tokens[0])) % 12 for t in tokens]
        readings = find_by_pcs(prog, tuple(pcs), rules)
        if not readings:
            print("No reading of these pitch classes is in the canonical enumeration.")
            print("Give octaves (e.g. C4 B3 D4 A4) or offsets to classify a specific register.")
            return 1
        cells = [p.cell for p in readings]
        print(f"{len(cells)} register reading(s) in the {prog.name} chapter:")
    for cell in cells:
        try:
            c = classify(cell, prog.interval)
        except CellError as e:
            print(f"invalid cell {cell}: {e}")
            return 1
        loc = locate(prog, cell, rules)
        where = (f"#{loc.index} of {len(enumerate_section(prog, loc.section, rules))}"
                 if loc else "not in the canonical enumeration")
        print(f"  {_spell_cell(prog, cell, sharps):28s} offsets {list(cell)}  {c.label}  ({where})")
    return 0


def cmd_midi(args) -> int:
    from .midi import to_midi

    prog, cell = _resolve(args)
    notes = realize(prog, cell, parse_midi(args.root), args.direction)
    data = to_midi(notes, tempo_bpm=args.tempo)
    out = Path(args.output or f"{prog.key}_{'_'.join(str(x) for x in cell[1:])}.mid")
    out.write_bytes(data)
    print(f"wrote {out} ({len(notes)} notes)")
    return 0


def cmd_abc(args) -> int:
    prog, cell = _resolve(args)
    sharps = spelling_sharps(prog, args.spelling)
    notes = realize(prog, cell, parse_midi(args.root), args.direction)
    c = classify(cell, prog.interval)
    sys.stdout.write(to_abc(notes, title=f"{prog.name}: {c.label}", sharps=sharps))
    return 0


def cmd_fit(args) -> int:
    rules = _rules(args)
    anchors = load_anchors(args.anchors)
    fits = fit(anchors, rules)
    if args.json:
        from .catalog import _fit_json

        print(json.dumps({"summary": fit_summary(fits), "sections": _fit_json(fits)}, indent=2))
        return 0
    for f in fits:
        marks = ", ".join(
            f"#{p.anchor.number}->{p.pattern.index}{'*' if p.relabelled else ''}" for p in f.placements
        )
        off = f"  book #{f.offset + 1}-{f.offset + f.size}" if f.verdict == "exact" else ""
        bad = "".join(f"  conflict: #{a.number}" for a in f.conflicts)
        print(f"{f.progression.name:17s} {f.label:34s} {f.verdict:12s} [{marks}]{off}{bad}")
    s = fit_summary(fits)
    print()
    print(f"{s['multiAnchorInOrder']}/{s['multiAnchorSections']} sections with 2+ anchors follow the "
          f"enumeration's order; {s['anchorsReproducedExactly']} anchors reproduced exactly; "
          f"{s['predictedNumbers']} book numbers predicted; {s['conflicts']} anchor(s) conflict with "
          f"their section.")
    print("(* = anchor moved to another section than its source heading; see docs/FINDINGS.md)")
    return 0


def cmd_catalog(args) -> int:
    from .catalog import build_catalog, dumps

    text = dumps(build_catalog(_rules(args)), compact=not args.pretty)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(text)
    return 0


def cmd_serve(args) -> int:
    from .server import serve

    serve(args.host, args.port, open_browser=args.open)
    return 0


def cmd_build_site(args) -> int:
    from .server import build_site

    path = build_site(Path(args.directory), single_file=args.single_file)
    print(f"wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="slonimsky", description="Slonimsky Thesaurus, reconstructed.")
    ap.add_argument("--contour", choices=["monotone", "any"], help="ordering rule for multi-note infra/ultrapolation")
    ap.add_argument("--max-notes", type=int, help="largest number of added notes per section (default 3)")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("chapters", help="list the twelve progressions").set_defaults(func=cmd_chapters)

    p = sub.add_parser("sections", help="list a chapter's sections")
    p.add_argument("progression")
    p.set_defaults(func=cmd_sections)

    def spelling(parser):
        parser.add_argument("--spelling", choices=["auto", "sharps", "flats"], default="auto")

    def realization(parser):
        parser.add_argument("--root", default="C4", help="starting note, e.g. C4, F#3, 60")
        parser.add_argument("--direction", choices=["up", "down", "updown"], default="up")

    p = sub.add_parser("list", help="list patterns of a chapter")
    p.add_argument("progression")
    p.add_argument("section", nargs="?", help="section key, e.g. infra-inter")
    p.add_argument("--limit", type=int, default=0)
    spelling(p)
    p.set_defaults(func=cmd_list)

    for name, func, helptext in (
        ("show", cmd_show, "explain and realize a pattern"),
        ("abc", cmd_abc, "print ABC notation"),
        ("midi", cmd_midi, "write a MIDI file"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("pattern", nargs="+", help="pattern id (ditone:-1,2,9) or progression + offsets")
        realization(p)
        spelling(p)
        if name == "show":
            p.add_argument("--abc", action="store_true", help="also print ABC notation")
        if name == "midi":
            p.add_argument("-o", "--output")
            p.add_argument("--tempo", type=float, default=100)
        p.set_defaults(func=func)

    p = sub.add_parser("classify", help="name a cell: offsets, notes with octaves, or note names")
    p.add_argument("progression")
    p.add_argument("notes", nargs="+", help="e.g. 0 -1 2 9 | C4 B3 D4 A4 | C B D A")
    spelling(p)
    p.set_defaults(func=cmd_classify)

    p = sub.add_parser("fit", help="test the reconstruction against known book numbers")
    p.add_argument("--anchors", help="alternative anchors CSV")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_fit)

    p = sub.add_parser("catalog", help="write the JSON catalog")
    p.add_argument("-o", "--output")
    p.add_argument("--pretty", action="store_true")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser("serve", help="run the web UI")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--open", action="store_true", help="open a browser")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("build-site", help="write the web UI as static files")
    p.add_argument("directory")
    p.add_argument("--single-file", action="store_true", help="inline everything into index.html")
    p.set_defaults(func=cmd_build_site)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (KeyError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except BrokenPipeError:  # e.g. `slonimsky list tritone | head`
        sys.stderr.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
