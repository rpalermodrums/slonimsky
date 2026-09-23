"""Regression tests for the research result: how well the rules fit the book."""

from slonimsky.anchors import fit, fit_summary, load_anchors, place, predictions
from slonimsky.thesaurus import Rules


def by_section(fits):
    return {(f.progression.key, f.key): f for f in fits}


def test_anchor_file_loads():
    anchors = load_anchors()
    assert len(anchors) >= 70
    numbers = [a.number for a in anchors]
    assert numbers == sorted(numbers)
    assert anchors[0].number == 1 and anchors[0].cell_pcs == (0, 1)


def test_exact_sections():
    fits = by_section(fit())
    expected = {
        ("sesquitone", "interpolation-1"): 391,
        ("sesquitone", "infra-inter"): 481,
        ("sesquitone", "inter-ultra"): 491,
        ("whole-tone", "ultrapolation-1"): 569,
        ("quinquetone", "ultrapolation-1"): 821,
    }
    for key, offset in expected.items():
        f = fits[key]
        assert f.verdict == "exact", key
        assert f.offset == offset, key


def test_conflicts_downgrade_a_section():
    fits = by_section(fit())
    iu = fits[("sesquitone", "infra-ultra")]
    assert iu.verdict == "mostly-exact" and iu.offset == 499 and iu.support == 4
    assert [a.number for a in iu.conflicts] == [508]
    assert sum(len(f.conflicts) for f in fits.values()) == 4


def test_every_multi_anchor_section_is_in_order():
    for rules in (Rules(), Rules(contour="any")):
        s = fit_summary(fit(rules=rules))
        assert s["multiAnchorSections"] >= 14
        assert s["multiAnchorInOrder"] == s["multiAnchorSections"]


def test_selection_sections():
    fits = by_section(fit())
    for key in [
        ("ditone", "infrapolation-3"),
        ("ditone", "infra-inter-ultra"),
        ("sesquitone", "ultrapolation-2"),
        ("sesquitone", "infrapolation-2"),
        ("quadritone", "interpolation-3"),
        ("sesquiquadritone", "interpolation-2"),
    ]:
        assert fits[key].verdict == "selection", key


def test_register_ambiguity_is_resolved_by_section_order():
    placed = {p.anchor.number: p for p in place(load_anchors())}
    assert placed[578].pattern.cell == (0, 11)  # ultrapolation: B above D
    assert placed[579].pattern.cell == (0, -1)  # infrapolation: B below C
    assert placed[579].relabelled
    assert placed[388].pattern is None  # "Miscellaneous Patterns" is not reconstructed


def test_predictions():
    pred = predictions(fit())
    assert pred["sesquitone:2,6"] == {"number": 498, "status": "predicted"}
    assert pred["sesquitone:2,7"] == {"number": 499, "status": "confirmed"}
    assert pred["whole-tone:4"]["number"] == 571
    assert pred["sesquitone:-5,2"]["number"] == 491
    assert "sesquitone:-1,5" not in pred  # sections with conflicts predict nothing


def test_signed_offsets_pin_the_register(tmp_path):
    csv = tmp_path / "a.csv"
    csv.write_text(
        "number,progression,label,cell,source,note\n"
        "599,whole-tone,,0 11,test,\n"
        "600,whole-tone,Ultrapolation of One Note,0 -1,test,\n"  # B below C: not an ultrapolation
    )
    placed = {p.anchor.number: p for p in place(load_anchors(str(csv)))}
    assert placed[599].pattern.cell == (0, 11)
    assert placed[600].pattern.cell == (0, -1) and placed[600].relabelled
