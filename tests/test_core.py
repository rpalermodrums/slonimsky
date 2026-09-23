import pytest

from slonimsky.analysis import analyze, interval_vector, prime_form, scale_name, transposition_count
from slonimsky.cells import CellError, classify, has_pc_repeat, parse_cell, section_key, section_label
from slonimsky.pitch import midi_name, parse_midi, parse_pc
from slonimsky.progressions import PROGRESSIONS, get_progression
from slonimsky.realize import realize


def test_twelve_chapters_are_equal_divisions():
    assert len(PROGRESSIONS) == 12
    assert sorted(p.interval for p in PROGRESSIONS) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14]
    for p in PROGRESSIONS:
        assert p.octaves * 12 == p.parts * p.interval


@pytest.mark.parametrize(
    "key,description",
    [
        ("tritone", "Equal Division of One Octave into Two Parts"),
        ("quadritone", "Equal Division of Two Octaves into Three Parts"),
        ("sesquiquadritone", "Equal Division of Three Octaves into Four Parts"),
        ("septitone", "Equal Division of Seven Octaves into Six Parts"),
        ("sesquiquinquetone", "Equal Division of Eleven Octaves into Twelve Parts"),
    ],
)
def test_book_descriptions(key, description):
    assert get_progression(key).description == description


def test_progression_lookup_aliases():
    assert get_progression("Whole Tone").key == "whole-tone"
    assert get_progression("fifths").interval == 7
    assert get_progression(9).key == "sesquiquadritone"
    assert get_progression("Ditone Progression").interval == 4
    with pytest.raises(KeyError):
        get_progression("heptatone")


@pytest.mark.parametrize(
    "cell,interval,label,key",
    [
        ((0, 1), 6, "Interpolation of One Note", "interpolation-1"),
        ((0, 5, 10, 7), 4, "Ultrapolation of Three Notes", "ultrapolation-3"),
        ((0, -1, -2), 3, "Infrapolation of Two Notes", "infrapolation-2"),
        ((0, -1, 1), 3, "Infra-Interpolation", "infra-inter"),
        ((0, 1, 5), 3, "Inter-Ultrapolation", "inter-ultra"),
        ((0, -1, 2, 9), 4, "Infra-Inter-Ultrapolation", "infra-inter-ultra"),
        ((0, 5, -1, 10), 8, "Inter-Infra-Ultrapolation", "inter-infra-ultra"),
        ((0, -1, -2, 1), 3, "Infra-Interpolation (2 + 1 notes)", "infra2-inter"),
    ],
)
def test_classification_matches_slonimsky_headings(cell, interval, label, key):
    c = classify(cell, interval)
    assert (c.label, c.key) == (label, key)


def test_invalid_cells():
    with pytest.raises(CellError):
        classify((0, 4), 4)  # lands on the next principal tone
    with pytest.raises(CellError):
        classify((1, 2), 4)  # must start on the principal tone


def test_section_label_of_no_roles():
    assert section_label(()) == "Principal Tones"
    assert section_key(()) == "principal"


def test_pc_repeats():
    assert has_pc_repeat((0, 12), 10)  # octave of the starting tone
    assert has_pc_repeat((0, -1), 11)  # B below C is the next principal's pitch class
    assert not has_pc_repeat((0, -1, 2, 9), 4)


def test_parse_helpers():
    assert parse_cell("0,-1,2,9") == (0, -1, 2, 9)
    assert parse_cell("-1 2 9") == (0, -1, 2, 9)
    assert parse_pc("Bb") == 10 and parse_pc("C#") == 1 and parse_pc("F♯") == 6
    assert parse_midi("C4") == 60 and parse_midi("A4") == 69 and parse_midi("Bb3") == 58
    assert midi_name(61, sharps=False) == "Db4"


def test_pattern_one_realization():
    # Thesaurus #1: C C# F# G C
    notes = realize(get_progression("tritone"), (0, 1), 60)
    assert [n.midi for n in notes] == [60, 61, 66, 67, 72]
    assert [n.role for n in notes] == ["P", "N", "P", "N", "P"]


def test_down_is_the_mirror_and_updown_retraces():
    prog = get_progression("tritone")
    down = realize(prog, (0, 1), 72, "down")
    assert [n.midi for n in down] == [72, 71, 66, 65, 60]
    updown = realize(prog, (0, 1), 60, "updown")
    assert [n.midi for n in updown] == [60, 61, 66, 67, 72, 67, 66, 61, 60]


def test_infra_goes_below_and_ultra_above():
    prog = get_progression("ditone")
    notes = [n.midi for n in realize(prog, (0, -1, 2, 9), 60)]
    assert notes[:5] == [60, 59, 62, 69, 64]


def test_multi_octave_cycles_are_folded():
    prog = get_progression("diatessaron")  # 5 octaves by default folded into 2
    midis = [n.midi for n in realize(prog, (0, 1), 60)]
    assert max(midis) < 60 + 24 + 6
    assert midis[-1] % 12 == 0
    unfolded = [n.midi for n in realize(prog, (0, 1), 60, fold=None)]
    assert unfolded[-1] == 60 + 60


def test_analysis_names_symmetric_scales():
    sesq = get_progression("sesquitone")
    assert analyze(sesq, (0, 1))["scale"] == "Octatonic (diminished) scale"
    ditone = get_progression("ditone")
    assert analyze(ditone, (0, 3))["scale"] == "Augmented (hexatonic) scale"
    tritone = get_progression("tritone")
    assert analyze(tritone, (0, 1, 2))["scale"] == "Two-semitone tritone scale (Messiaen mode 5)"
    assert analyze(ditone, (0, -1, 2, 9))["twelveTone"]


def test_named_sets_are_distinct_set_classes():
    from slonimsky.analysis import _NAMED_SETS

    primes = [prime_form(v) for v in _NAMED_SETS.values()]
    assert len(set(primes)) == len(primes)


def test_set_theory():
    assert prime_form([0, 4, 7]) == (0, 3, 7)  # major and minor triads share 3-11
    assert prime_form([0, 3, 7]) == (0, 3, 7)
    assert prime_form([0, 1, 3, 4, 6, 7, 9, 10]) == (0, 1, 3, 4, 6, 7, 9, 10)
    assert interval_vector([0, 4, 7]) == (0, 0, 1, 1, 1, 0)
    assert transposition_count([0, 2, 4, 6, 8, 10]) == 2
    assert scale_name([2, 4, 6, 7, 9, 11, 1]) == "Diatonic collection"
