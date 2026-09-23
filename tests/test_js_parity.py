"""The browser engine (web/engine.js) must agree with the Python package.

Skipped when Node.js is not installed.
"""

import json
import shutil
import subprocess
from importlib import resources

import pytest

from slonimsky.analysis import analyze
from slonimsky.cells import classify, describe
from slonimsky.notation import to_abc
from slonimsky.progressions import PROGRESSIONS
from slonimsky.realize import realize, spelling_sharps
from slonimsky.thesaurus import build_chapter

node = shutil.which("node")
pytestmark = pytest.mark.skipif(node is None, reason="Node.js not installed")


def sample_cases():
    cases = []
    for prog in PROGRESSIONS:
        for section in build_chapter(prog).sections:
            for p in section.patterns[:: max(1, len(section.patterns) // 3)]:
                for direction in ("up", "down", "updown"):
                    cases.append((prog, p.cell, direction))
    return cases


def test_engine_matches_python(tmp_path):
    cases = sample_cases()
    payload = [
        {"prog": {"interval": p.interval, "parts": p.parts, "octaves": p.octaves},
         "cell": list(c), "direction": d, "root": 57}
        for p, c, d in cases
    ]
    engine = resources.files("slonimsky").joinpath("web/engine.js")
    script = tmp_path / "run.js"
    script.write_text(
        "const E = require(%s);\n"
        "const cases = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n"
        "const out = cases.map(c => {\n"
        "  const notes = E.realize(c.prog, c.cell, c.root, c.direction);\n"
        "  const sharps = E.spellingSharps(c.prog.interval, 'auto');\n"
        "  return { notes: notes.map(n => [n.midi, n.role, n.group]),\n"
        "    abc: E.toAbc(notes, 'T', sharps), cls: E.classify(c.cell, c.prog.interval),\n"
        "    desc: E.describe(c.cell, c.prog.interval), an: E.analyze(c.prog, c.cell) };\n"
        "});\n"
        "process.stdout.write(JSON.stringify(out));\n" % json.dumps(str(engine))
    )
    res = subprocess.run([node, str(script)], input=json.dumps(payload), capture_output=True,
                         text=True, check=True)
    js = json.loads(res.stdout)
    assert len(js) == len(cases)
    for (prog, cell, direction), got in zip(cases, js):
        notes = realize(prog, cell, 57, direction)
        assert got["notes"] == [[n.midi, n.role, n.group] for n in notes], (prog.key, cell, direction)
        assert got["abc"] == to_abc(notes, "T", spelling_sharps(prog)), (prog.key, cell)
        assert got["cls"] == classify(cell, prog.interval).to_dict()
        assert got["desc"] == describe(cell, prog.interval)
        a = analyze(prog, cell)
        assert got["an"] == {k: (list(v) if isinstance(v, tuple) else v) for k, v in a.items()}
