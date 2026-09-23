import json
import struct
import threading
import urllib.request

import pytest

from slonimsky.catalog import build_catalog, dumps
from slonimsky.cli import main
from slonimsky.midi import to_midi
from slonimsky.notation import to_abc
from slonimsky.progressions import get_progression
from slonimsky.realize import realize


def test_abc_bars_and_accidentals():
    notes = realize(get_progression("tritone"), (0, 1), 60)
    abc = to_abc(notes, sharps=True)
    assert abc.splitlines()[-1] == "C^C | ^FG | c |]"
    # within a bar, a natural cancels an earlier sharp on the same line and octave
    notes = realize(get_progression("ditone"), (0, -1, 2, 9), 60)
    assert "^G=G" in to_abc(notes, sharps=True)
    assert "A_B" in to_abc(realize(get_progression("sesquitone"), (0, 1), 60), sharps=False)


def test_abc_octaves_and_clef():
    notes = realize(get_progression("tritone"), (0, 1), 36)
    abc = to_abc(notes)
    assert "clef=bass" in abc and "C,," in abc


def test_midi_file_structure():
    notes = realize(get_progression("tritone"), (0, 1), 60)
    data = to_midi(notes, tempo_bpm=120)
    assert data[:4] == b"MThd"
    fmt, ntrk, tpq = struct.unpack(">HHH", data[8:14])
    assert (fmt, ntrk, tpq) == (0, 1, 480)
    assert data[14:18] == b"MTrk"
    (length,) = struct.unpack(">I", data[18:22])
    assert len(data) == 22 + length
    assert data.count(bytes([0x90, 61])) == 1
    assert data.endswith(b"\xff\x2f\x00")


def test_catalog_json():
    cat = json.loads(dumps(build_catalog()))
    assert cat["total"] == sum(p["count"] for p in cat["progressions"])
    ses = next(p for p in cat["progressions"] if p["key"] == "sesquitone")
    nu = next(s for s in ses["sections"] if s["key"] == "inter-ultra")
    assert [p["book"]["number"] for p in nu["patterns"]] == list(range(492, 500))
    assert cat["fitSummary"]["multiAnchorInOrder"] == cat["fitSummary"]["multiAnchorSections"]


def test_cli_commands(capsys, tmp_path):
    assert main(["chapters"]) == 0
    assert "Septitone" in capsys.readouterr().out
    assert main(["show", "ditone:-1,2,9"]) == 0
    out = capsys.readouterr().out
    assert "Infra-Inter-Ultrapolation" in out and "C4 B3 D4 A4 E4" in out
    assert main(["classify", "whole-tone", "C", "B"]) == 0
    assert "2 register reading(s)" in capsys.readouterr().out
    assert main(["classify", "ditone", "C4", "B3", "D4", "A4"]) == 0
    assert "#10 of" in capsys.readouterr().out
    out_file = tmp_path / "p.mid"
    assert main(["midi", "tritone", "1", "-o", str(out_file)]) == 0
    assert out_file.read_bytes()[:4] == b"MThd"
    assert main(["fit"]) == 0
    assert "sections with 2+ anchors follow" in capsys.readouterr().out
    assert main(["show", "nonsense", "1"]) == 2


def test_server_routes():
    from slonimsky.server import make_server

    httpd = make_server("127.0.0.1", 0)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        with urllib.request.urlopen(base + "/") as r:
            assert b"Slonimsky" in r.read()
        with urllib.request.urlopen(base + "/data/catalog.json") as r:
            assert json.loads(r.read())["total"] > 3000
        with urllib.request.urlopen(base + "/api/midi?id=ditone:-1,2,9&tempo=90") as r:
            assert r.headers["Content-Type"] == "audio/midi" and r.read()[:4] == b"MThd"
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(base + "/../pyproject.toml")
        assert e.value.code == 404
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_build_site(tmp_path):
    from slonimsky.server import build_site

    single = build_site(tmp_path / "one", single_file=True)
    html = single.read_text()
    assert "window.SLONIMSKY_CATALOG" in html and 'src="app.js"' not in html
    multi = build_site(tmp_path / "multi")
    assert (multi.parent / "data" / "catalog.json").exists()
    assert (multi.parent / "vendor" / "abcjs-basic-min.js").exists()
