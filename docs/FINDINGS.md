# Is there an algorithm behind Slonimsky's Thesaurus?

Short answer: **mostly yes for the structure and the order, no for the
selection.** A small set of rules generates every pattern type in the
progression chapters, and the book's patterns appear in the order those
rules list them: exactly (number for number) where a section is small, and
as an in-order *subset* where a section is large. What Slonimsky left out of
the large sections doesn't follow any rule the available data can pin down.

Everything below can be re-run with `slonimsky fit` and is covered by
`tests/test_anchors.py`.

## 1. What the previous version got wrong

The original TypeScript app modelled a pattern as *division × interpolation
type × ultrapolation semitones*. That isn't Slonimsky's system:

* **Interpolation was an equal subdivision** (`stepSize = P / (count + 1)`),
  which produces fractional semitones (a tritone with four interpolated notes
  moved in 1.2-semitone steps; the test suite compared sums with
  `toBeCloseTo`). In the book, interpolated notes are *chosen* chromatic
  notes: pattern #1 is C C♯ F♯ G, #392 is C D♭ E♭ E …
* **Ultrapolation was a neighbour-note ornament** (+k then −k around each
  principal tone), and infrapolation was treated as "ultrapolation below".
  Slonimsky's terms are about *where* an added note sits relative to the two
  principal tones: infrapolation below the current one, interpolation
  between them, ultrapolation above the next one.
* **Only five one-octave divisions.** The book has twelve chapters, seven of
  them multi-octave (two octaves ÷ 3, three ÷ 4, five ÷ 6, five ÷ 12,
  seven ÷ 6, seven ÷ 12, eleven ÷ 12).
* **No contact with the book.** The catalog was a parameter grid with no
  ordering and no way to compare it with Slonimsky's numbering, which is the
  only evidence an algorithm could leave behind.

## 2. The model

A pattern is a **cell**: semitone offsets from a principal tone, starting at
0. The cell is repeated on every principal tone of an equal division of N
octaves into M parts (principal interval P, `N·12 = M·P`). Each added note
has a role by position:

| role | offset | Slonimsky |
| --- | --- | --- |
| `I` | < 0 | infrapolation |
| `N` | 0 < x < P | interpolation |
| `U` | > P | ultrapolation |

The book's section headings follow from the roles in playing order:
C B D A → E (Ditone) is `(0, −1, 2, 9)` = I, N, U = "Infra-Inter-Ultrapolation".
One role repeated gives "Ultrapolation of Three Notes" and so on.
`slonimsky classify ditone C4 B3 D4 A4` does this for any cell.

## 3. Evidence: anchors

An *anchor* is a published fact tying a book number to a pattern. There are
71 of them in `src/slonimsky/data/anchors.csv`:

* 66 from **Gotham & Yust's *Serial Analyser* anthology**, which lists the
  Thesaurus patterns whose first twelve notes form a twelve-tone row, with
  number, heading and pitch classes. The cell is recovered as the shortest
  prefix that repeats up by P (`scripts/fetch_anchors.py`).
* 5 widely cited facts: #1 = C C♯ F♯ G; #392/#393 = the two octatonic
  scales; #10 is a two-note interpolation; #286 (Giant Steps) is a ditone
  infra-interpolation (Bair 2003).
* Chapter ranges: Tritone #1–180, Ditone #181–391, Sesquitone #392–568.

Two biases matter. The sources give **pitch classes, not register**, so
C B in the whole-tone chapter could be B above D (ultrapolation) or B below
C (infrapolation); the fit tries every reading. And the anthology only
contains **twelve-tone** patterns, so most patterns in any section are
invisible to it.

## 4. The reconstruction

`src/slonimsky/thesaurus.py` generates each chapter from these rules:

1. **Sections, in book order:** Interpolation of 1..3 notes, Ultrapolation
   of 1..3, Infrapolation of 1..3, Infra-Inter, Inter-Ultra, Infra-Ultra,
   Infra-Inter-Ultra, Inter-Infra-Ultra. (Every anchor pair across sections
   respects this order.)
2. **Windows, nearest note first.** Interpolation: every note between the
   principal tones. Single-role infra/ultrapolation: out to an octave span,
   `max(11 − P, 3)` semitones. Mixed sections: ultrapolations up to one
   semitone past the principal tone after next (`P + 1`), infrapolations
   one further (`P + 2`).
3. **Lexicographic order**, with earlier notes varying slowest.
4. **No repeated pitch class** within a cell (counting the next principal
   tone). This is what makes the quinquetone skip C in its ultrapolation:
   #822 = B, #823 = D♭.
5. **Monotone contours** for multi-note infra/ultrapolation (the default),
   or every contour grouped by shape (`--contour any`), which is the only
   ordering that keeps the book's zig-zag ditone ultrapolations (#216, #221,
   #230) in order.

That gives 3,680 patterns, about 2.7× the ~1,100 in the book's progression
chapters.

## 5. Results

### Sections the rules reproduce exactly

| chapter | section | anchors | book numbers |
| --- | --- | --- | --- |
| Sesquitone | Interpolation of One Note | #392, #393 | 392–393 |
| Sesquitone | Infra-Interpolation | #482, #485 | 482–491 |
| Sesquitone | Inter-Ultrapolation | #493, #496, #499 | 492–499 |
| Whole-Tone | Ultrapolation of One Note | #570 #572 #574 #576 #578 | 570–578 |
| Quinquetone | Ultrapolation of One Note | #822, #823 | 822–823 |

Two cross-checks that weren't fitted:

* The Infra-Interpolation grid (5 infra × 2 inter = 10) ends exactly at #491,
  and Inter-Ultrapolation independently starts at #492.
* Whole-Tone ultrapolation of one note ends at #578, and #579 is the first
  infrapolation of one note (B below C). The order holds, but the book goes
  straight from one to the other, so this chapter has no two- or three-note
  ultrapolations at that point. Which sections a chapter contains varies from
  chapter to chapter.

These fits yield **31 predicted book numbers** (dashed badges in the UI), for
example #483 = C B D → E♭, #494 = C D♭ G♭ → E♭, #571 = C E → D (whole-tone).
Anyone with the book can check them.

Sesquitone Infra-Ultrapolation also matches four anchors exactly (#500, #503,
#505, #512 on one 5×4 grid) but **#508 contradicts it**: the anthology gives
C B♭ A♭, while the grid predicts C A E. Either the grid isn't complete there
or the source row is off. The section is marked "mostly exact" and makes no
predictions.

### Everywhere else, the book is an in-order selection

In **all 14 sections with two or more anchors**, the book's patterns come in
the same order as the canonical enumeration. In the 7 marked "selection"
the book skips patterns between anchors, so it lists a subset in that order.
If the book's order within a section had nothing to do with the enumeration,
this would be very unlikely. The Sesquitone "Ultrapolation of Two Notes"
alone has six anchors, a 1-in-720 chance of falling in order. Across all 14
sections it is about 1 in 10¹⁶, though sections with only two anchors add
little on their own. The within-section **order** is algorithmic: nearest
note first, earlier notes varying slowest.

What decides which patterns are **omitted** is still open. Two observations
for whoever picks this up:

* Sesquitone Ultrapolation of Two Notes: #405/#415, #407/#417 and #410/#420
  differ by exactly 10, and in each pair the first note moves up by one
  principal interval (3 semitones). In Infrapolation of Two Notes, shifting
  both notes down by 3 moves #453→#466 and #456→#469 (+13). This suggests
  the book lays these sections out in blocks, one per principal interval of
  distance, and probably repeats the same selection inside each block.
* The Ditone Infra-Inter-Ultrapolation anchors cover 31 book numbers
  (#340–#371) where the enumeration has 49 cells (#10–#59), so about 63 % are
  kept, and the gaps aren't uniform.

### Anchors that don't fit

| # | chapter | heading in source | cell (from C) | note |
| --- | --- | --- | --- | --- |
| 508 | Sesquitone | Infra-Ultrapolation | C B♭ A♭ | see above |
| 736 | Quadritone | Inter-Infra-Ultrapolation | C D G A | reads as inter, inter, ultra |
| 795 | Sesquiquadritone | Infra-Ultrapolation | C A♭ D♭ | needs wider windows |
| 875 | Quinquetone | Infrapolation of One Note | C G♭ F B | 4-note cell; heading probably stale in source |

Also outside the model: #799 ("Infra-Infrapolation", C D G), #903 and #909
(quinquetone cells of 6 and 8 notes), and the Miscellaneous and Permutations
sections (#388–391, #637–657, #915), which aren't generated at all.

## 6. What would settle it

The missing piece is **complete ground truth for a few sections**, not more
theory. For example the Tritone chapter (#1–180), or Sesquitone
#394–481, transcribed as

```
number, chapter, heading, first cell (e.g. "C Db F")
```

would show exactly which patterns the book omits from the in-order
sections, and whether the omissions follow a rule (symmetry? repeated
pitch-class sets? something visual on the page?). Add rows to
`src/slonimsky/data/anchors.csv` (signed offsets such as `0 -1 +2 +9` pin the
register) and run `slonimsky fit`.
