/*
 * Slonimsky engine (browser mirror of the Python package).
 *
 * Python is the source of truth: it builds the catalog (which patterns
 * exist, their order, book numbers). This file only re-implements the
 * small pure functions the UI needs to be interactive offline: realizing
 * a cell into notes, spelling, ABC notation, classifying a hand-built
 * cell and analysing its pitch-class set. tests/test_js_parity.py checks
 * every function here against its Python twin.
 */
(function (root) {
  "use strict";

  var SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  var FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
  var SHARP_PREFERRED = [1, 2, 4, 6, 7, 9, 14];
  var NUMBER_WORDS = {
    1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
    8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve",
  };
  var ROLE_PREFIX = { I: "Infra", N: "Inter", U: "Ultra" };
  var ROLE_WORD = { I: "infrapolation", N: "interpolation", U: "ultrapolation" };

  function mod12(x) {
    return ((x % 12) + 12) % 12;
  }

  function pcName(pc, sharps) {
    return (sharps ? SHARP_NAMES : FLAT_NAMES)[mod12(pc)];
  }

  function midiName(midi, sharps) {
    return pcName(midi, sharps) + (Math.floor(midi / 12) - 1);
  }

  function prefersSharps(interval) {
    return SHARP_PREFERRED.indexOf(interval) >= 0;
  }

  function spellingSharps(interval, preference) {
    if (preference === "sharps") return true;
    if (preference === "flats") return false;
    return prefersSharps(interval);
  }

  // ---------------------------------------------------------------- cells
  function roleOf(offset, interval) {
    if (offset < 0) return "I";
    if (offset > 0 && offset < interval) return "N";
    if (offset > interval) return "U";
    throw new Error("offset " + offset + " coincides with a principal tone");
  }

  function rolesOf(cell, interval) {
    if (!cell.length || cell[0] !== 0) throw new Error("a cell must start with offset 0");
    return cell.slice(1).map(function (x) {
      return roleOf(x, interval);
    });
  }

  function runs(roles) {
    var out = [];
    roles.forEach(function (r) {
      if (out.length && out[out.length - 1][0] === r) out[out.length - 1][1] += 1;
      else out.push([r, 1]);
    });
    return out;
  }

  function capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function sectionLabel(roles) {
    if (!roles.length) return "Principal Tones";
    var rs = runs(roles);
    if (rs.length === 1) {
      var n = rs[0][1];
      return capitalize(ROLE_WORD[rs[0][0]]) + " of " + (NUMBER_WORDS[n] || n) + (n === 1 ? " Note" : " Notes");
    }
    var words = rs.map(function (x) {
      return ROLE_PREFIX[x[0]];
    });
    var label = words.slice(0, -1).join("-") + "-" + capitalize(ROLE_WORD[rs[rs.length - 1][0]]);
    if (rs.some(function (x) { return x[1] > 1; })) {
      label += " (" + rs.map(function (x) { return x[1]; }).join(" + ") + " notes)";
    }
    return label;
  }

  function sectionKey(roles) {
    if (!roles.length) return "principal";
    var rs = runs(roles);
    if (rs.length === 1) return ROLE_WORD[rs[0][0]] + "-" + rs[0][1];
    return rs
      .map(function (x) {
        var p = ROLE_PREFIX[x[0]].toLowerCase();
        return x[1] === 1 ? p : p + x[1];
      })
      .join("-");
  }

  function classify(cell, interval) {
    var roles = rolesOf(cell, interval);
    return { roles: roles, key: sectionKey(roles), label: sectionLabel(roles) };
  }

  function hasPcRepeat(cell, interval) {
    var seen = {};
    var full = cell.concat([interval]);
    for (var i = 0; i < full.length; i++) {
      var p = mod12(full[i]);
      if (seen[p]) return true;
      seen[p] = true;
    }
    return false;
  }

  function describe(cell, interval) {
    return cell.map(function (x, i) {
      if (i === 0) return { offset: 0, role: "P", text: "principal tone" };
      var r = roleOf(x, interval);
      var text =
        r === "I" ? -x + " below the principal tone"
        : r === "N" ? x + " above the principal tone"
        : x - interval + " above the next principal tone";
      return { offset: x, role: r, text: text };
    });
  }

  // -------------------------------------------------------------- realize
  function defaultFold(prog) {
    return prog.octaves > 2 ? 2 : null;
  }

  function realize(prog, cell, rootMidi, direction, fold) {
    if (rootMidi === undefined) rootMidi = 60;
    direction = direction || "up";
    if (fold === undefined || fold === "auto") fold = defaultFold(prog);
    var sign = direction === "down" ? -1 : 1;
    var P = prog.interval;
    var M = prog.parts;
    var notes = [];
    for (var k = 0; k <= M; k++) {
      var base = k * P;
      if (fold) {
        var span = 12 * fold;
        if (base >= span) base = base % span;
      }
      var offsets = k < M ? cell : [0];
      for (var j = 0; j < offsets.length; j++) {
        var x = offsets[j];
        notes.push({ midi: rootMidi + sign * (base + x), role: x === 0 ? "P" : roleOf(x, P), group: k });
      }
    }
    if (direction === "updown") {
      notes = notes.concat(notes.slice(0, -1).reverse());
    }
    return notes;
  }

  // ------------------------------------------------------------------ ABC
  var ABC_SHARP = ["C", "^C", "D", "^D", "E", "F", "^F", "G", "^G", "A", "^A", "B"];
  var ABC_FLAT = ["C", "_D", "D", "_E", "E", "F", "_G", "G", "_A", "A", "_B", "B"];

  function abcPitch(midi, sharps, state) {
    var token = (sharps ? ABC_SHARP : ABC_FLAT)[mod12(midi)];
    var acc = token.length === 2 ? token[0] : "=";
    var letter = token.length === 2 ? token[1] : token;
    var octave = Math.floor(midi / 12) - 1;
    var key = letter + octave;
    var current = state[key] === undefined ? "=" : state[key];
    var shown = current === acc ? "" : acc;
    state[key] = acc;
    var body;
    if (octave >= 5) body = letter.toLowerCase() + "'".repeat(octave - 5);
    else body = letter + ",".repeat(4 - octave);
    return shown + body;
  }

  function toAbc(notes, title, sharps, barsPerLine, unit) {
    if (sharps === undefined) sharps = true;
    barsPerLine = barsPerLine || 4;
    unit = unit || "1/8";
    var midis = notes.map(function (n) { return n.midi; }).sort(function (a, b) { return a - b; });
    var median = midis.length ? midis[Math.floor(midis.length / 2)] : 60;
    var clef = median < 57 ? "bass" : "treble";
    var header = ["X:1"];
    if (title) header.push("T:" + title);
    header.push("M:none", "L:" + unit, "K:C clef=" + clef);
    var bars = [];
    var current = [];
    var state = {};
    var group = notes.length ? notes[0].group : 0;
    notes.forEach(function (n) {
      if (n.group !== group) {
        bars.push(current.join(""));
        current = [];
        state = {};
        group = n.group;
      }
      current.push(abcPitch(n.midi, sharps, state));
    });
    if (current.length) bars.push(current.join(""));
    var lines = [];
    for (var i = 0; i < bars.length; i += barsPerLine) {
      var chunk = bars.slice(i, i + barsPerLine);
      var end = i + barsPerLine >= bars.length ? " |]" : " |";
      lines.push(chunk.join(" | ") + end);
    }
    return header.concat(lines).join("\n") + "\n";
  }

  // ------------------------------------------------------------- analysis
  function pcSet(values) {
    var seen = {};
    values.forEach(function (v) { seen[mod12(v)] = true; });
    return Object.keys(seen).map(Number).sort(function (a, b) { return a - b; });
  }

  function cyclePcs(prog, cell) {
    var vals = [];
    for (var k = 0; k < prog.parts; k++) {
      cell.forEach(function (x) { vals.push(k * prog.interval + x); });
    }
    return pcSet(vals);
  }

  function rowPrefix(prog, cell, length) {
    length = length || 12;
    var out = [];
    for (var k = 0; out.length < length; k++) {
      for (var j = 0; j < cell.length && out.length < length; j++) {
        out.push(mod12(k * prog.interval + cell[j]));
      }
    }
    return out;
  }

  function isTwelveTone(prog, cell) {
    return pcSet(rowPrefix(prog, cell, 12)).length === 12;
  }

  function lexLess(a, b) {
    for (var i = 0; i < Math.min(a.length, b.length); i++) {
      if (a[i] !== b[i]) return a[i] < b[i];
    }
    return a.length < b.length;
  }

  function normalForm(pcs) {
    var s = pcSet(pcs);
    var n = s.length;
    if (n <= 1) return s;
    var best = null;
    var bestKey = null;
    for (var i = 0; i < n; i++) {
      var rot = s.slice(i).concat(s.slice(0, i).map(function (p) { return p + 12; }));
      var key = [];
      for (var j = n - 1; j > 0; j--) key.push(rot[j] - rot[0]);
      if (best === null || lexLess(key, bestKey)) {
        best = rot;
        bestKey = key;
      }
    }
    return best.map(mod12);
  }

  function primeForm(pcs) {
    var s = pcSet(pcs);
    if (!s.length) return [];
    var cands = [s, pcSet(s.map(function (p) { return -p; }))].map(function (v) {
      var nf = normalForm(v);
      return nf.map(function (p) { return mod12(p - nf[0]); });
    });
    var ra = cands[0].slice().reverse();
    var rb = cands[1].slice().reverse();
    return lexLess(rb, ra) ? cands[1] : cands[0];
  }

  function intervalVector(pcs) {
    var s = pcSet(pcs);
    var vec = [0, 0, 0, 0, 0, 0];
    for (var i = 0; i < s.length; i++) {
      for (var j = i + 1; j < s.length; j++) {
        var d = mod12(s[j] - s[i]);
        vec[Math.min(d, 12 - d) - 1] += 1;
      }
    }
    return vec;
  }

  function transpositionCount(pcs) {
    var s = pcSet(pcs);
    var seen = {};
    for (var t = 0; t < 12; t++) {
      seen[pcSet(s.map(function (p) { return p + t; })).join(",")] = true;
    }
    return Object.keys(seen).length;
  }

  var NAMED_SETS = [
    ["Chromatic scale", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]],
    ["Whole-tone scale", [0, 2, 4, 6, 8, 10]],
    ["Octatonic (diminished) scale", [0, 1, 3, 4, 6, 7, 9, 10]],
    ["Augmented (hexatonic) scale", [0, 3, 4, 7, 8, 11]],
    ["Tritone scale", [0, 1, 4, 6, 7, 10]],
    ["Two-semitone tritone scale (Messiaen mode 5)", [0, 1, 2, 6, 7, 8]],
    ["Messiaen mode 3", [0, 2, 3, 4, 6, 7, 8, 10, 11]],
    ["Messiaen mode 4", [0, 1, 2, 5, 6, 7, 8, 11]],
    ["Messiaen mode 6", [0, 2, 4, 5, 6, 8, 10, 11]],
    ["Messiaen mode 7", [0, 1, 2, 3, 5, 6, 7, 8, 9, 11]],
    ["Diatonic collection", [0, 2, 4, 5, 7, 9, 11]],
    ["Acoustic (melodic minor) collection", [0, 2, 3, 5, 7, 9, 11]],
    ["Harmonic minor collection", [0, 2, 3, 5, 7, 8, 11]],
    ["Pentatonic collection", [0, 2, 4, 7, 9]],
    ["Diminished seventh chord", [0, 3, 6, 9]],
    ["Augmented triad", [0, 4, 8]],
    ["Tritone", [0, 6]],
  ];
  var BY_PRIME = {};
  NAMED_SETS.forEach(function (e) { BY_PRIME[primeForm(e[1]).join(",")] = e[0]; });

  function scaleName(pcs) {
    return BY_PRIME[primeForm(pcs).join(",")] || null;
  }

  function analyze(prog, cell) {
    var pcs = cyclePcs(prog, cell);
    return {
      pcs: pcs,
      cardinality: pcs.length,
      primeForm: primeForm(pcs),
      intervalVector: intervalVector(pcs),
      transpositions: transpositionCount(pcs),
      scale: scaleName(pcs),
      twelveTone: isTwelveTone(prog, cell),
    };
  }

  var api = {
    SHARP_NAMES: SHARP_NAMES,
    FLAT_NAMES: FLAT_NAMES,
    mod12: mod12,
    pcName: pcName,
    midiName: midiName,
    prefersSharps: prefersSharps,
    spellingSharps: spellingSharps,
    roleOf: roleOf,
    rolesOf: rolesOf,
    sectionLabel: sectionLabel,
    sectionKey: sectionKey,
    classify: classify,
    hasPcRepeat: hasPcRepeat,
    describe: describe,
    defaultFold: defaultFold,
    realize: realize,
    toAbc: toAbc,
    cyclePcs: cyclePcs,
    rowPrefix: rowPrefix,
    isTwelveTone: isTwelveTone,
    primeForm: primeForm,
    intervalVector: intervalVector,
    transpositionCount: transpositionCount,
    scaleName: scaleName,
    analyze: analyze,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.SlonimskyEngine = api;
})(this);
