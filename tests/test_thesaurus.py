from slonimsky.cells import has_pc_repeat, roles_of
from slonimsky.progressions import PROGRESSIONS, get_progression
from slonimsky.thesaurus import (
    DEFAULT_RULES,
    Rules,
    SectionSpec,
    build_chapter,
    enumerate_section,
    find_by_pcs,
    locate,
    parse_pattern_id,
    pattern_id,
)


def keys(prog):
    return [s.spec.key for s in build_chapter(prog).sections]


def test_section_order_follows_the_book():
    assert keys(get_progression("tritone")) == [
        "interpolation-1", "interpolation-2", "interpolation-3",
        "ultrapolation-1", "ultrapolation-2", "ultrapolation-3",
        "infrapolation-1", "infrapolation-2", "infrapolation-3",
        "infra-inter", "inter-ultra", "infra-ultra", "infra-inter-ultra", "inter-infra-ultra",
    ]
    # nothing fits between the principal tones of the semitone progression
    assert "interpolation-1" not in keys(get_progression("semitone"))


def test_single_note_sections_are_complete_and_nearest_first():
    tritone = get_progression("tritone")
    inter = enumerate_section(tritone, SectionSpec(("N",)))
    assert inter == ((0, 1), (0, 2), (0, 3), (0, 4), (0, 5))
    wt = get_progression("whole-tone")
    ultra = enumerate_section(wt, SectionSpec(("U",)))
    assert [c[1] for c in ultra] == list(range(3, 12))  # #570-578 in the book
    infra = enumerate_section(wt, SectionSpec(("I",)))
    assert infra[0] == (0, -1)


def test_mixed_sections_are_products_in_role_order():
    sesq = get_progression("sesquitone")
    nu = enumerate_section(sesq, SectionSpec(("N", "U")))
    assert nu == tuple((0, n, u) for n in (1, 2) for u in (4, 5, 6, 7))  # #492-499
    ii = enumerate_section(sesq, SectionSpec(("I", "N")))
    assert len(ii) == 10 and ii[0] == (0, -1, 1) and ii[3] == (0, -2, 2)  # #482-491


def test_monotone_contours():
    ditone = get_progression("ditone")
    for cell in enumerate_section(ditone, SectionSpec(("I", "I", "I"))):
        assert cell[1] > cell[2] > cell[3]  # stepping further down
    for cell in enumerate_section(ditone, SectionSpec(("U", "U"))):
        assert cell[1] > cell[2] > ditone.interval  # descending onto the next principal


def test_any_contour_includes_zigzags_grouped_by_shape():
    ditone = get_progression("ditone")
    rules = Rules(contour="any")
    cells = enumerate_section(ditone, SectionSpec(("U", "U", "U")), rules)
    assert len(cells) == 35 * 6
    assert (0, 5, 10, 7) in cells and (0, 6, 5, 11) in cells
    # Book #216 < #221 < #230: the shape-grouped order keeps them in order
    idx = [cells.index(c) for c in ((0, 5, 10, 7), (0, 6, 11, 9), (0, 6, 5, 11))]
    assert idx == sorted(idx)


def test_no_pitch_class_repeats_and_valid_roles_everywhere():
    for prog in PROGRESSIONS:
        for section in build_chapter(prog).sections:
            for p in section.patterns:
                assert not has_pc_repeat(p.cell, prog.interval)
                assert roles_of(p.cell, prog.interval) == section.spec.roles


def test_ids_round_trip_and_locate():
    ditone = get_progression("ditone")
    pid = pattern_id(ditone, (0, -1, 2, 9))
    assert pid == "ditone:-1,2,9"
    assert parse_pattern_id(pid) == (ditone, (0, -1, 2, 9))
    loc = locate(ditone, (0, -1, 2, 9))
    assert loc.section.label == "Infra-Inter-Ultrapolation" and loc.index == 10
    assert locate(ditone, (0, 11, 2)) is None  # 11 is outside the mixed ultra window


def test_register_readings():
    wt = get_progression("whole-tone")
    readings = find_by_pcs(wt, (0, 11))
    assert [(r.section.key, r.cell) for r in readings] == [
        ("ultrapolation-1", (0, 11)),
        ("infrapolation-1", (0, -1)),
    ]


def test_windows():
    assert DEFAULT_RULES.single_window(3) == 8
    assert DEFAULT_RULES.single_window(10) == 3
    assert DEFAULT_RULES.mixed_window(3, "I") == 5
    assert DEFAULT_RULES.mixed_window(3, "U") == 4
    assert DEFAULT_RULES.mixed_window(9, "U") == 3


def test_catalog_size_is_stable():
    total = sum(len(s.patterns) for p in PROGRESSIONS for s in build_chapter(p).sections)
    assert total == 3680
