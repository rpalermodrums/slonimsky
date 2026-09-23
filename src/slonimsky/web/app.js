/*
 * Slonimsky Thesaurus Lab: the single-page UI.
 * Data: window.SLONIMSKY_CATALOG (single-file build) or data/catalog.json.
 */
(function () {
  "use strict";

  var E = window.SlonimskyEngine;
  var AudioLib = window.SlonimskyAudio;
  var player = new AudioLib.Player();
  var app = document.getElementById("app");

  var ROLE_NAME = { P: "principal", I: "infrapolation", N: "interpolation", U: "ultrapolation" };
  var ROLE_SHORT = { P: "principal", I: "infra", N: "inter", U: "ultra" };
  var VERDICT_TEXT = {
    exact: "exact",
    selection: "in order",
    single: "1 anchor",
    "mostly-exact": "mostly exact",
    reordered: "reordered",
    none: "none",
  };
  var SCALE_ABBR = {
    "Chromatic scale": "chromatic",
    "Whole-tone scale": "whole-tone",
    "Octatonic (diminished) scale": "octatonic",
    "Augmented (hexatonic) scale": "hexatonic",
    "Tritone scale": "tritone sc.",
    "Two-semitone tritone scale (Messiaen mode 5)": "2-st tritone",
    "Diatonic collection": "diatonic",
  };

  // ---------------------------------------------------------------- state
  var S = {
    catalog: null,
    progs: {},
    patterns: {}, // id -> {prog, section, p}
    view: "thesaurus",
    progKey: "tritone",
    sectionKey: null,
    patternId: null,
    spelling: store("spelling", "auto"),
    filter: { q: "", rows: false, book: false },
    bpm: +store("bpm", 96),
    perBeat: +store("perBeat", 2),
    direction: store("direction", "up"),
    rootPc: +store("rootPc", 0),
    rootOct: +store("rootOct", 4),
    loop: store("loop", "1") === "1",
    metronome: store("metronome", "0") === "1",
    cycleKeys: store("cycleKeys", "off"),
    learned: new Set(JSON.parse(store("learned", "[]"))),
    builder: { progKey: "ditone", cell: [0, -1, 2, 9] },
    researchContour: "monotone",
    playingIndex: -1,
    current: null, // {prog, cell, notes, id, title}
  };

  function store(key, fallback) {
    try {
      var v = localStorage.getItem("slonimsky." + key);
      return v === null ? fallback : v;
    } catch (e) {
      return fallback;
    }
  }
  function save(key, value) {
    try {
      localStorage.setItem("slonimsky." + key, value);
    } catch (e) {
      /* storage unavailable: settings just won't persist */
    }
  }

  // ------------------------------------------------------------------ dom
  function h(tag, attrs) {
    var el = document.createElement(tag);
    var kids = Array.prototype.slice.call(arguments, 2);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v === null || v === undefined || v === false) return;
        if (k === "class") el.className = v;
        else if (k === "html") el.innerHTML = v;
        else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v);
        else el.setAttribute(k, v === true ? "" : v);
      });
    }
    append(el, kids);
    return el;
  }
  function append(el, kids) {
    kids.forEach(function (c) {
      if (c === null || c === undefined || c === false) return;
      if (Array.isArray(c)) append(el, c);
      else el.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
    });
  }
  var SVGNS = "http://www.w3.org/2000/svg";
  function s(tag, attrs) {
    var el = document.createElementNS(SVGNS, tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (attrs[k] !== null && attrs[k] !== undefined) el.setAttribute(k, attrs[k]);
    });
    Array.prototype.slice.call(arguments, 2).forEach(function (c) {
      if (c) el.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return el;
  }
  function icon(name) {
    var paths = {
      play: "M8 5v14l11-7z",
      stop: "M6 6h12v12H6z",
      prev: "M15 6l-6 6 6 6",
      next: "M9 6l6 6-6 6",
      shuffle: "M4 7h3l10 10h3M4 17h3l3-3M14 10l3-3h3M17 4l3 3-3 3M17 14l3 3-3 3",
      download: "M12 4v11M7 10l5 5 5-5M5 20h14",
      copy: "M9 9h10v10H9zM5 15V5h10",
      build: "M4 20l6-6M14 4l6 6-8 8-6-6z",
    };
    var filled = name === "play" || name === "stop";
    return s("svg", { viewBox: "0 0 24 24", "aria-hidden": "true",
      style: filled ? "" : "fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round" },
      s("path", { d: paths[name] }));
  }

  // --------------------------------------------------------------- helpers
  function sharpsFor(prog) {
    return E.spellingSharps(prog.interval, S.spelling);
  }
  function rootMidi() {
    return 12 * (S.rootOct + 1) + S.rootPc;
  }
  function cellNodes(prog, cell, rootPc) {
    var sharps = sharpsFor(prog);
    var out = [];
    cell.forEach(function (x, i) {
      var role = i === 0 ? "P" : E.roleOf(x, prog.interval);
      if (i) out.push(" ");
      out.push(h("span", { class: "r-" + role }, E.pcName((rootPc || 0) + x, sharps)));
    });
    out.push(h("span", { class: "arrow" }, " → "));
    out.push(h("span", { class: "r-P" }, E.pcName((rootPc || 0) + prog.interval, sharps)));
    return out;
  }
  function cellText(prog, cell) {
    var sharps = sharpsFor(prog);
    return cell.map(function (x) { return E.pcName(x, sharps); }).join(" ") + " → " + E.pcName(prog.interval, sharps);
  }
  function bookBadge(book) {
    if (!book) return null;
    var title = book.status === "confirmed"
      ? "Thesaurus pattern " + book.number + " (confirmed by a published source)"
      : "Predicted Thesaurus pattern " + book.number + " (from an exactly-fitting section)";
    return h("span", { class: "book " + book.status, title: title }, "№ " + book.number);
  }
  function idFor(prog, cell) {
    return prog.key + ":" + cell.slice(1).join(",");
  }
  function sectionOf(prog, key) {
    for (var i = 0; i < prog.sections.length; i++) if (prog.sections[i].key === key) return prog.sections[i];
    return null;
  }

  // -------------------------------------------------------------- routing
  var currentHash = "";
  function parseHash(hash) {
    currentHash = hash === undefined ? location.hash : hash;
    var parts = currentHash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
    var view = parts[0] || "thesaurus";
    if (["thesaurus", "builder", "research", "about"].indexOf(view) < 0) view = "thesaurus";
    S.view = view;
    if (view === "thesaurus") {
      var rec = parts[3] && S.patterns[parts[3]];
      if (rec) {
        // the pattern decides its own chapter and section
        S.progKey = rec.prog.key;
        S.sectionKey = rec.section.key;
        S.patternId = parts[3];
        return;
      }
      if (parts[1] && S.progs[parts[1]]) S.progKey = parts[1];
      var prog = S.progs[S.progKey];
      S.sectionKey = parts[2] && sectionOf(prog, parts[2]) ? parts[2] : prog.sections[0].key;
      S.patternId = sectionOf(prog, S.sectionKey).patterns[0].id;
    } else if (view === "builder") {
      if (parts[1] && S.progs[parts[1]]) S.builder.progKey = parts[1];
      if (parts[2] !== undefined) {
        var cell = [0].concat(parts[2].split(",").filter(Boolean).map(Number));
        if (cell.every(function (x) { return !isNaN(x); })) S.builder.cell = cell;
      }
    }
  }
  function go(hash) {
    if (currentHash === hash) return render();
    try {
      location.hash = hash;
    } catch (e) {
      /* some embeds refuse hash changes */
    }
    if (location.hash !== hash) {
      parseHash(hash); // navigate in memory instead
      render();
    }
  }
  function patternHash(id) {
    var rec = S.patterns[id];
    return "#/thesaurus/" + rec.prog.key + "/" + rec.section.key + "/" + id;
  }

  // ------------------------------------------------------------ rendering
  function render() {
    player.stop();
    S.playingIndex = -1;
    document.querySelectorAll(".tabs a").forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("data-view") === S.view);
    });
    app.innerHTML = "";
    if (S.view === "thesaurus") renderThesaurus();
    else if (S.view === "builder") renderBuilder();
    else if (S.view === "research") renderResearch();
    else renderAbout();
  }

  function chapterIcon(prog, size) {
    size = size || 34;
    var r = 13, c = 16;
    var svg = s("svg", { viewBox: "0 0 32 32", width: size, height: size, "aria-hidden": "true" });
    svg.appendChild(s("circle", { cx: c, cy: c, r: r, fill: "none", stroke: "var(--line-2)", "stroke-width": 1.4 }));
    var pts = [];
    for (var k = 0; k < prog.parts; k++) {
      var pc = (k * prog.interval) % 12;
      var a = (pc / 12) * 2 * Math.PI - Math.PI / 2;
      pts.push((c + r * Math.cos(a)).toFixed(2) + "," + (c + r * Math.sin(a)).toFixed(2));
    }
    if (pts.length > 2) {
      svg.appendChild(s("polygon", { points: pts.join(" "), fill: "none", stroke: "var(--accent)", "stroke-width": 1.6, "stroke-linejoin": "round" }));
    } else {
      svg.appendChild(s("polyline", { points: pts.join(" "), fill: "none", stroke: "var(--accent)", "stroke-width": 1.6 }));
    }
    return svg;
  }

  function renderThesaurus() {
    var prog = S.progs[S.progKey];
    var section = sectionOf(prog, S.sectionKey);
    var rec = S.patterns[S.patternId];

    var chapters = h("nav", { class: "card chapters", "aria-label": "Chapters" });
    S.catalog.progressions.forEach(function (p) {
      var active = p.key === prog.key;
      chapters.appendChild(h("button", {
        class: "chapter" + (active ? " active" : ""),
        onclick: function () { go("#/thesaurus/" + p.key); },
        title: p.description,
      },
        chapterIcon(p),
        h("span", null,
          h("div", { class: "c-name" }, p.name),
          h("div", { class: "c-meta" }, "P = " + p.interval + " · " + p.octaves + " oct ÷ " + p.parts)),
        h("span", { class: "c-count" }, p.count)));
      if (active) {
        var list = h("div", { class: "sections" });
        p.sections.forEach(function (sec) {
          list.appendChild(h("button", {
            class: "section-link" + (sec.key === section.key ? " active" : ""),
            onclick: function () { go("#/thesaurus/" + p.key + "/" + sec.key); },
          }, h("span", null, sec.label), h("span", { class: "n" }, sec.patterns.length)));
        });
        chapters.appendChild(list);
      }
    });

    var listBody = h("div", { class: "plist-body", role: "listbox", "aria-label": "Patterns" });
    var q = S.filter.q.trim().toLowerCase();
    var shown = section.patterns.filter(function (p) {
      if (S.filter.rows && !p.row) return false;
      if (S.filter.book && !p.book) return false;
      if (!q) return true;
      var text = (cellText(prog, p.cell) + " " + (p.scale || "") + " " + (p.book ? p.book.number : "")).toLowerCase();
      return q.split(/\s+/).every(function (t) { return text.indexOf(t) >= 0; });
    });
    shown.forEach(function (p) {
      var badges = h("span", { class: "badges" });
      if (p.book) badges.appendChild(bookBadge(p.book));
      if (p.row) badges.appendChild(h("span", { class: "tag", title: "First twelve notes form a twelve-tone row" }, "12"));
      if (p.scale && SCALE_ABBR[p.scale]) badges.appendChild(h("span", { class: "tag" }, SCALE_ABBR[p.scale]));
      listBody.appendChild(h("button", {
        class: "prow" + (p.id === S.patternId ? " active" : "") + (S.learned.has(p.id) ? " learned" : ""),
        role: "option",
        "aria-selected": p.id === S.patternId ? "true" : "false",
        onclick: function () { go(patternHash(p.id)); },
      }, h("span", { class: "idx" }, p.i), h("span", { class: "cellnames" }, cellNodes(prog, p.cell)), badges));
    });
    if (!shown.length) listBody.appendChild(h("p", { class: "muted", style: "padding:12px" }, "No patterns match."));

    var search = h("input", { type: "search", placeholder: "Filter: notes, scale, №…", value: S.filter.q,
      "aria-label": "Filter patterns",
      oninput: function (e) {
        S.filter.q = e.target.value;
        var pos = e.target.selectionStart;
        render();
        var el = document.querySelector(".plist-tools input[type=search]");
        el.focus();
        el.setSelectionRange(pos, pos);
      } });
    var plist = h("section", { class: "card plist" },
      h("div", { class: "plist-head" },
        h("div", { class: "eyebrow" }, prog.title),
        h("h2", null, section.label),
        h("div", { class: "muted", style: "font-size:13px" },
          shown.length + " of " + section.patterns.length + " patterns · canonical order"),
        h("div", { class: "plist-tools" }, search,
          checkbox("12-tone rows", S.filter.rows, function (v) { S.filter.rows = v; render(); }),
          checkbox("Book №", S.filter.book, function (v) { S.filter.book = v; render(); }))),
      listBody);

    var detail = h("section", { class: "detail" });
    app.appendChild(h("div", { class: "thesaurus" }, chapters, plist, detail));
    if (rec) {
      renderDetail(detail, {
        prog: prog,
        cell: rec.p.cell,
        id: rec.p.id,
        sectionLabel: section.label,
        index: rec.p.i,
        size: section.patterns.length,
        book: rec.p.book,
        inThesaurus: true,
      });
    }
    var active = listBody.querySelector(".prow.active");
    if (active && active.scrollIntoView) active.scrollIntoView({ block: "nearest" });
  }

  function checkbox(label, checked, onchange) {
    var input = h("input", { type: "checkbox", onchange: function (e) { onchange(e.target.checked); } });
    input.checked = checked;
    return h("label", { class: "check" }, input, label);
  }

  // --------------------------------------------------------------- detail
  function describeCell(prog, cell) {
    var sharps = sharpsFor(prog);
    var roles = {};
    E.describe(cell, prog.interval).slice(1).forEach(function (d) {
      (roles[d.role] = roles[d.role] || []).push(d);
    });
    var bits = [];
    function names(list) {
      return list.map(function (d) { return E.pcName(S.rootPc + d.offset, sharps); }).join(", ");
    }
    if (roles.I) bits.push("drops below the principal tone to " + names(roles.I));
    if (roles.N) bits.push("fills in " + names(roles.N) + " between the principal tones");
    if (roles.U) bits.push("overshoots the next principal tone to " + names(roles.U));
    if (!bits.length) return "The bare principal tones.";
    var t = "Each cell " + bits.join(", then ") + ".";
    return t.charAt(0).toUpperCase() + t.slice(1);
  }

  function realizeCurrent(prog, cell) {
    return E.realize(prog, cell, rootMidi(), S.direction);
  }

  function renderDetail(container, m) {
    var prog = m.prog;
    var sharps = sharpsFor(prog);
    var notes = realizeCurrent(prog, m.cell);
    var classification = E.classify(m.cell, prog.interval);
    S.current = { prog: prog, cell: m.cell, notes: notes, id: m.id, label: classification.label };

    var chips = h("div", { class: "derivation" });
    E.describe(m.cell, prog.interval).forEach(function (d) {
      chips.appendChild(h("span", { class: "chip r-" + d.role, title: d.text },
        h("b", null, E.pcName(S.rootPc + d.offset, sharps)),
        h("small", null, ROLE_SHORT[d.role] + (d.offset ? " " + (d.offset > 0 ? "+" : "") + d.offset : ""))));
    });
    chips.appendChild(h("span", { class: "chip r-P", title: "next principal tone" },
      h("b", null, E.pcName(S.rootPc + prog.interval, sharps)), h("small", null, "next +" + prog.interval)));

    var bookLine;
    if (m.book) {
      bookLine = h("span", null, bookBadge(m.book), " ",
        h("span", { class: "muted", style: "font-size:13px" },
          m.book.status === "confirmed" ? "confirmed book number" : "predicted book number"));
    } else if (m.inThesaurus) {
      bookLine = h("span", { class: "muted", style: "font-size:13px" }, "book number unknown");
    }

    var head = h("div", { class: "card dhead" },
      h("div", { class: "crumbs" },
        h("b", null, prog.title), "›", h("span", null, m.sectionLabel || classification.label),
        m.index ? h("span", null, "› " + m.index + " of " + m.size) : null),
      h("div", { class: "dtitle" }, h("span", { class: "big" }, cellNodes(prog, m.cell, S.rootPc)), bookLine),
      h("p", { class: "dsub" }, prog.description + ". " + describeCell(prog, m.cell)),
      chips);

    var scoreEl = h("div", { class: "score", "aria-label": "Notation" });
    var transport = renderTransport(prog, m);
    var scoreCard = h("div", { class: "card" }, scoreEl, transport);

    var visuals = h("div", { class: "visuals" },
      h("div", { class: "card clock" }, renderClock(prog, m.cell)),
      h("div", { class: "card keys" }, renderKeyboard(notes),
        h("div", { class: "legend" },
          h("span", { class: "l-P" }, "principal"), h("span", { class: "l-N" }, "interpolation"),
          h("span", { class: "l-I" }, "infrapolation"), h("span", { class: "l-U" }, "ultrapolation"))));

    var a = E.analyze(prog, m.cell);
    var row = E.rowPrefix(prog, m.cell, 12).map(function (p) { return E.pcName(p + S.rootPc, sharps); }).join(" ");
    var facts = h("div", { class: "facts" },
      fact("Collection", a.scale || "—"),
      fact("Pitch classes", a.cardinality + " of 12"),
      fact("Prime form", "(" + a.primeForm.join(",") + ")", true),
      fact("Interval vector", "<" + a.intervalVector.join("") + ">", true),
      fact("Symmetry", a.transpositions < 12 ? a.transpositions + " transpositions (symmetric)" : "none (12 transpositions)"),
      fact("Twelve-tone row", a.twelveTone ? "yes: " + row : "no"),
      fact("Cell offsets", "[" + m.cell.join(", ") + "] → " + prog.interval, true),
      fact("Section", classification.label));

    container.appendChild(head);
    container.appendChild(scoreCard);
    container.appendChild(visuals);
    container.appendChild(facts);
    container.appendChild(renderPractice(m));
    drawScore(scoreEl, prog, notes, m);
  }

  function fact(label, value, mono) {
    return h("div", { class: "fact" }, h("div", { class: "eyebrow" }, label), h("div", { class: "v" + (mono ? " mono" : "") }, value));
  }

  function drawScore(el, prog, notes, m) {
    el.innerHTML = "";
    var sharps = sharpsFor(prog);
    if (window.ABCJS && window.ABCJS.renderAbc) {
      var width = Math.max(260, Math.min((el.clientWidth || 700) - 40, 860));
      var abc = E.toAbc(notes, "", sharps, width < 520 ? 2 : notes.length > 40 ? 4 : 6);
      window.ABCJS.renderAbc(el, abc, {
        staffwidth: width,
        add_classes: true,
        foregroundColor: getComputedStyle(document.documentElement).getPropertyValue("--ink").trim() || "#000",
        paddingtop: 6, paddingbottom: 6, paddingleft: 4, paddingright: 4,
      });
      var els = el.querySelectorAll(".abcjs-note");
      notes.forEach(function (n, i) {
        if (els[i]) els[i].classList.add("role-" + n.role);
      });
    } else {
      var box = h("div", { class: "score-fallback" });
      notes.forEach(function (n, i) {
        if (i && notes[i - 1].group !== n.group) box.appendChild(document.createTextNode(" | "));
        box.appendChild(h("span", { class: "r-" + n.role }, E.midiName(n.midi, sharps)));
        box.appendChild(document.createTextNode(" "));
      });
      el.appendChild(box);
    }
  }

  function highlight(i) {
    S.playingIndex = i;
    var score = document.querySelector(".score");
    if (!score) return;
    var els = score.querySelectorAll(".abcjs-note, .score-fallback span");
    els.forEach(function (e, k) { e.classList.toggle("is-playing", k === i); });
    var dots = document.querySelectorAll(".key-dot");
    var midi = S.current && S.current.notes[i] ? S.current.notes[i].midi : null;
    dots.forEach(function (d) { d.classList.toggle("is-playing", +d.getAttribute("data-midi") === midi); });
  }

  function renderTransport(prog, m) {
    var playBtn = h("button", { class: "btn primary", id: "play-btn", onclick: togglePlay }, icon("play"), "Play");
    var bpmLabel = h("span", { class: "bpm" }, S.bpm);
    var bpm = h("input", { type: "range", min: 30, max: 260, value: S.bpm, "aria-label": "Tempo",
      oninput: function (e) { S.bpm = +e.target.value; bpmLabel.textContent = S.bpm; save("bpm", S.bpm); } });
    var rootSel = h("select", { "aria-label": "Root note", onchange: function (e) {
      S.rootPc = +e.target.value; save("rootPc", S.rootPc); render(); } });
    for (var pc = 0; pc < 12; pc++) {
      var o = h("option", { value: pc }, E.pcName(pc, sharpsFor(prog)));
      if (pc === S.rootPc) o.selected = true;
      rootSel.appendChild(o);
    }
    var octSel = h("select", { "aria-label": "Octave", onchange: function (e) {
      S.rootOct = +e.target.value; save("rootOct", S.rootOct); render(); } });
    [2, 3, 4, 5].forEach(function (oc) {
      var o = h("option", { value: oc }, String(oc));
      if (oc === S.rootOct) o.selected = true;
      octSel.appendChild(o);
    });
    function seg(options, value, onpick) {
      var box = h("div", { class: "seg", role: "group" });
      options.forEach(function (opt) {
        box.appendChild(h("button", { type: "button", "aria-pressed": opt[0] === value ? "true" : "false",
          onclick: function () { onpick(opt[0]); } }, opt[1]));
      });
      return box;
    }
    return h("div", { class: "transport" },
      playBtn,
      h("span", { class: "field" }, "Tempo", bpm, bpmLabel),
      h("span", { class: "field" }, "Start", rootSel, octSel),
      seg([["up", "Up"], ["down", "Down"], ["updown", "Up & back"]], S.direction, function (v) {
        S.direction = v; save("direction", v); render(); }),
      seg([[2, "♪ 8ths"], [3, "3 trip."], [4, "♬ 16ths"]], S.perBeat, function (v) {
        S.perBeat = v; save("perBeat", v); render(); }),
      h("button", { class: "btn small", "aria-pressed": S.loop ? "true" : "false", onclick: function (e) {
        S.loop = !S.loop; save("loop", S.loop ? "1" : "0"); e.currentTarget.setAttribute("aria-pressed", S.loop); } }, "Loop"),
      h("button", { class: "btn small", "aria-pressed": S.metronome ? "true" : "false", onclick: function (e) {
        S.metronome = !S.metronome; save("metronome", S.metronome ? "1" : "0");
        e.currentTarget.setAttribute("aria-pressed", S.metronome); } }, "Click"));
  }

  function setPlayButton(playing) {
    var b = document.getElementById("play-btn");
    if (!b) return;
    b.innerHTML = "";
    b.appendChild(icon(playing ? "stop" : "play"));
    b.appendChild(document.createTextNode(playing ? "Stop" : "Play"));
  }

  function togglePlay() {
    if (player.playing) {
      player.stop();
      setPlayButton(false);
      highlight(-1);
      return;
    }
    if (!S.current) return;
    setPlayButton(true);
    player.play(S.current.notes, {
      bpm: S.bpm,
      perBeat: S.perBeat,
      loop: S.loop,
      metronome: S.metronome,
      onNote: highlight,
      onLoop: function () {
        if (S.cycleKeys === "off") return null;
        var step = S.cycleKeys === "fourths" ? 5 : 1;
        S.rootPc = (S.rootPc + step) % 12;
        save("rootPc", S.rootPc);
        var cur = S.current;
        cur.notes = realizeCurrent(cur.prog, cur.cell);
        var scoreEl = document.querySelector(".score");
        if (scoreEl) drawScore(scoreEl, cur.prog, cur.notes, cur);
        var sel = document.querySelector('select[aria-label="Root note"]');
        if (sel) sel.value = S.rootPc;
        var big = document.querySelector(".dtitle .big");
        if (big) { big.innerHTML = ""; append(big, cellNodes(cur.prog, cur.cell, S.rootPc)); }
        return cur.notes;
      },
      onEnd: function () { setPlayButton(false); highlight(-1); },
    });
  }

  function renderPractice(m) {
    var bar = h("div", { class: "card practice" });
    if (m.inThesaurus) {
      var learned = S.learned.has(m.id);
      bar.appendChild(h("button", { class: "btn small", "aria-pressed": learned ? "true" : "false",
        title: "Keyboard: L", onclick: toggleLearned }, learned ? "✓ Learned" : "Mark learned"));
      bar.appendChild(h("button", { class: "btn small", onclick: function () { step(-1); }, title: "Keyboard: ←" }, icon("prev"), "Prev"));
      bar.appendChild(h("button", { class: "btn small", onclick: function () { step(1); }, title: "Keyboard: →" }, "Next", icon("next")));
      bar.appendChild(h("button", { class: "btn small", onclick: randomPattern, title: "Keyboard: R" }, icon("shuffle"), "Random"));
    }
    var cyc = h("select", { "aria-label": "Cycle keys while looping", onchange: function (e) {
      S.cycleKeys = e.target.value; save("cycleKeys", S.cycleKeys); } });
    [["off", "Stay in key"], ["fourths", "Loop through keys by 4ths"], ["chromatic", "Loop through keys chromatically"]].forEach(function (o) {
      var opt = h("option", { value: o[0] }, o[1]);
      if (o[0] === S.cycleKeys) opt.selected = true;
      cyc.appendChild(opt);
    });
    bar.appendChild(cyc);
    bar.appendChild(h("span", { style: "flex:1" }));
    if (!window.SLONIMSKY_NO_DOWNLOADS) {
      bar.appendChild(h("button", { class: "btn small", onclick: downloadMidi }, icon("download"), "MIDI"));
    }
    bar.appendChild(h("button", { class: "btn small", onclick: copyAbc }, icon("copy"), "ABC"));
    if (m.inThesaurus) {
      bar.appendChild(h("button", { class: "btn small", onclick: function () {
        go("#/builder/" + m.prog.key + "/" + m.cell.slice(1).join(","));
      } }, icon("build"), "Edit in Builder"));
    }
    if (S.learned.size) bar.appendChild(h("span", { class: "muted", style: "font-size:13px" }, S.learned.size + " learned"));
    return bar;
  }

  function toggleLearned() {
    if (!S.current || !S.current.id) return;
    if (S.learned.has(S.current.id)) S.learned.delete(S.current.id);
    else S.learned.add(S.current.id);
    save("learned", JSON.stringify(Array.from(S.learned)));
    render();
  }

  function step(delta) {
    var prog = S.progs[S.progKey];
    var all = [];
    prog.sections.forEach(function (sec) { sec.patterns.forEach(function (p) { all.push(p.id); }); });
    var i = all.indexOf(S.patternId);
    var j = Math.max(0, Math.min(all.length - 1, i + delta));
    go(patternHash(all[j]));
  }

  function randomPattern() {
    var prog = S.progs[S.progKey];
    var pool = [];
    prog.sections.forEach(function (sec) {
      sec.patterns.forEach(function (p) { if (!S.learned.has(p.id)) pool.push(p.id); });
    });
    if (!pool.length) pool = Object.keys(S.patterns);
    go(patternHash(pool[Math.floor(Math.random() * pool.length)]));
  }

  function downloadMidi() {
    if (!S.current) return;
    var data = AudioLib.toMidi(S.current.notes, S.bpm, S.perBeat);
    var blob = new Blob([data], { type: "audio/midi" });
    var a = h("a", { href: URL.createObjectURL(blob), download: "slonimsky_" + S.current.prog.key + "_" +
      S.current.cell.slice(1).join("_").replace(/-/g, "m") + ".mid" });
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  function copyAbc() {
    if (!S.current) return;
    var cur = S.current;
    var abc = E.toAbc(cur.notes, cur.prog.name + ": " + cur.label, sharpsFor(cur.prog));
    var done = function () { toast("ABC notation copied"); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(abc).then(done, function () { fallbackCopy(abc); done(); });
    } else {
      fallbackCopy(abc);
      done();
    }
  }
  function fallbackCopy(text) {
    var ta = h("textarea", { style: "position:fixed;opacity:0" });
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) { /* ignore */ }
    ta.remove();
  }
  function toast(msg) {
    var t = h("div", { style: "position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:8px 14px;border-radius:8px;z-index:50;font-size:14px" }, msg);
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 1600);
  }

  // ------------------------------------------------------------- visuals
  function renderClock(prog, cell) {
    var sharps = sharpsFor(prog);
    var size = 220, c = size / 2, R = 84;
    var svg = s("svg", { viewBox: "0 0 " + size + " " + size, role: "img",
      "aria-label": "Pitch-class clock: principal tones and the first cell" });
    function pt(pc, rad) {
      var a = (E.mod12(pc) / 12) * 2 * Math.PI - Math.PI / 2;
      return [c + rad * Math.cos(a), c + rad * Math.sin(a)];
    }
    svg.appendChild(s("circle", { cx: c, cy: c, r: R, fill: "none", stroke: "var(--line-2)", "stroke-width": 1 }));
    var principal = [];
    for (var k = 0; k < prog.parts; k++) principal.push(E.mod12(S.rootPc + k * prog.interval));
    var polyPts = principal.map(function (pc) { return pt(pc, R).map(function (v) { return v.toFixed(1); }).join(","); });
    svg.appendChild(s(principal.length > 2 ? "polygon" : "polyline", { points: polyPts.join(" "), fill: "none",
      stroke: "var(--ink-3)", "stroke-width": 1.2, "stroke-dasharray": "3 3" }));
    var all = E.cyclePcs(prog, cell).map(function (p) { return E.mod12(p + S.rootPc); });
    // the path of the first cell, ending on the next principal tone
    var path = cell.concat([prog.interval]).map(function (x) { return pt(S.rootPc + x, R); });
    var d = path.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" ");
    svg.appendChild(s("path", { d: d, fill: "none", stroke: "var(--accent)", "stroke-width": 2, "stroke-linejoin": "round", opacity: 0.85 }));
    for (var pc = 0; pc < 12; pc++) {
      var lp = pt(pc, R + 17);
      var inSet = all.indexOf(pc) >= 0;
      svg.appendChild(s("text", { x: lp[0].toFixed(1), y: (lp[1] + 4).toFixed(1), "text-anchor": "middle",
        "font-size": 11.5, "font-family": "var(--mono)", fill: inSet ? "var(--ink)" : "var(--ink-3)",
        "font-weight": inSet ? 700 : 400 }, E.pcName(pc, sharps)));
      var dp = pt(pc, R);
      svg.appendChild(s("circle", { cx: dp[0].toFixed(1), cy: dp[1].toFixed(1), r: inSet ? 3.2 : 2,
        fill: inSet ? "var(--ink-2)" : "var(--line-2)" }));
    }
    cell.forEach(function (x, i) {
      var role = i === 0 ? "P" : E.roleOf(x, prog.interval);
      var p = pt(S.rootPc + x, R);
      svg.appendChild(s("circle", { cx: p[0].toFixed(1), cy: p[1].toFixed(1), r: 7.5,
        fill: "var(--role-" + role + ")", stroke: "var(--panel)", "stroke-width": 2 }));
      svg.appendChild(s("text", { x: p[0].toFixed(1), y: (p[1] + 3.5).toFixed(1), "text-anchor": "middle",
        "font-size": 9.5, "font-weight": 700, fill: "var(--panel)" }, String(i + 1)));
    });
    var np = pt(S.rootPc + prog.interval, R);
    svg.appendChild(s("circle", { cx: np[0].toFixed(1), cy: np[1].toFixed(1), r: 7.5, fill: "none",
      stroke: "var(--role-P)", "stroke-width": 2 }));
    svg.appendChild(s("text", { x: c, y: c - 4, "text-anchor": "middle", "font-size": 12, fill: "var(--ink-2)",
      "font-family": "var(--serif)" }, prog.name));
    svg.appendChild(s("text", { x: c, y: c + 12, "text-anchor": "middle", "font-size": 10.5, fill: "var(--ink-3)" },
      all.length + " pitch classes"));
    return svg;
  }

  function renderKeyboard(notes) {
    var midis = notes.map(function (n) { return n.midi; });
    var lo = Math.min.apply(null, midis), hi = Math.max.apply(null, midis);
    lo = lo - E.mod12(lo) ; // start on a C
    hi = hi + (11 - E.mod12(hi)); // end on a B
    var isBlack = function (m) { return [1, 3, 6, 8, 10].indexOf(E.mod12(m)) >= 0; };
    var whites = [];
    for (var m = lo; m <= hi; m++) if (!isBlack(m)) whites.push(m);
    var W = 20, H = 86, BW = 12, BH = 54;
    var svg = s("svg", { viewBox: "0 0 " + whites.length * W + " " + (H + 2), role: "img", "aria-label": "Keyboard" });
    var xOf = {};
    whites.forEach(function (mm, i) {
      xOf[mm] = i * W;
      svg.appendChild(s("rect", { class: "key-w", x: i * W + 0.5, y: 0.5, width: W - 1, height: H, rx: 2.5 }));
      if (E.mod12(mm) === 0) svg.appendChild(s("text", { x: i * W + W / 2, y: H - 6, "text-anchor": "middle",
        "font-size": 8.5, fill: "#8a8479" }, "C" + (Math.floor(mm / 12) - 1)));
    });
    for (m = lo; m <= hi; m++) {
      if (!isBlack(m)) continue;
      xOf[m] = xOf[m - 1] + W - BW / 2;
      svg.appendChild(s("rect", { class: "key-b", x: xOf[m], y: 0.5, width: BW, height: BH, rx: 2 }));
    }
    var seen = {};
    notes.forEach(function (n) {
      if (seen[n.midi]) return;
      seen[n.midi] = true;
      var black = isBlack(n.midi);
      var cx = xOf[n.midi] + (black ? BW / 2 : W / 2);
      var cy = black ? BH - 10 : H - 22;
      svg.appendChild(s("circle", { class: "key-dot", "data-midi": n.midi, cx: cx, cy: cy, r: black ? 4.6 : 5.4,
        fill: "var(--role-" + n.role + ")" }));
    });
    return svg;
  }

  // -------------------------------------------------------------- builder
  function renderBuilder() {
    var prog = S.progs[S.builder.progKey];
    var cell = S.builder.cell;
    var w = S.catalog.windows[prog.key];
    var reach = Math.max(w.single, 5);
    var sharps = sharpsFor(prog);

    var progSel = h("select", { "aria-label": "Progression", onchange: function (e) {
      S.builder.progKey = e.target.value;
      S.builder.cell = [0];
      go("#/builder/" + e.target.value + "/");
    } });
    S.catalog.progressions.forEach(function (p) {
      var o = h("option", { value: p.key }, p.title + " (P = " + p.interval + ")");
      if (p.key === prog.key) o.selected = true;
      progSel.appendChild(o);
    });

    function keyBtn(offset, role) {
      var used = cell.indexOf(offset) > 0;
      var principal = role === "P";
      return h("button", {
        class: "zkey r-" + role + (used ? " used" : "") + (principal ? " principal" : ""),
        title: principal ? "principal tone" : (used ? "remove " : "add ") + ROLE_NAME[role] + " (" + (offset > 0 ? "+" : "") + offset + ")",
        disabled: principal ? true : null,
        onclick: principal ? null : function () {
          var c = cell.slice();
          var i = c.indexOf(offset);
          if (i > 0) c.splice(i, 1);
          else c.push(offset);
          go("#/builder/" + prog.key + "/" + c.slice(1).join(","));
        },
      }, h("b", null, E.pcName(offset, sharps)), h("small", null, (offset > 0 ? "+" : "") + offset));
    }
    function zone(label, role, offsets) {
      return h("div", { class: "zone" }, h("div", { class: "zlabel r-" + role }, label),
        h("div", { class: "zkeys" }, offsets.map(function (o) { return keyBtn(o, role); })));
    }
    var infra = [], inter = [], ultra = [];
    for (var i = reach; i >= 1; i--) infra.push(-i);
    for (i = 1; i < prog.interval; i++) inter.push(i);
    for (i = 1; i <= reach; i++) ultra.push(prog.interval + i);
    var ruler = h("div", { class: "ruler" },
      zone("infra", "I", infra), zone("", "P", [0]), inter.length ? zone("inter", "N", inter) : null,
      zone("", "P", [prog.interval]), zone("ultra", "U", ultra));

    var chips = h("div", { class: "cellbar" }, h("span", { class: "eyebrow" }, "Cell, in playing order"));
    cell.forEach(function (x, idx) {
      var role = idx === 0 ? "P" : E.roleOf(x, prog.interval);
      chips.appendChild(h("span", { class: "cellchip r-" + role }, E.pcName(x, sharps) + " " + (idx ? (x > 0 ? "+" : "") + x : "0"),
        idx ? h("button", { "aria-label": "remove", onclick: function () {
          var c = cell.slice(); c.splice(idx, 1);
          go("#/builder/" + prog.key + "/" + c.slice(1).join(","));
        } }, "×") : null));
    });
    chips.appendChild(h("button", { class: "btn small", onclick: function () { go("#/builder/" + prog.key + "/"); } }, "Clear"));

    var id = idFor(prog, cell);
    var rec = S.patterns[id];
    var verdict = h("div", { class: "verdict" });
    var detailBox = h("section", { class: "detail" });
    if (cell.length > 1) {
      var cls = E.classify(cell, prog.interval);
      if (rec) {
        append(verdict, [h("b", null, cls.label), " · #" + rec.p.i + " of " + rec.section.patterns.length +
          " in the canonical enumeration ", rec.p.book ? bookBadge(rec.p.book) : null, " ",
          h("a", { href: patternHash(id) }, "open in Thesaurus")]);
      } else {
        append(verdict, [h("b", null, cls.label), " · ", h("span", { class: "muted" }, whyOutside(prog, cell))]);
      }
    } else {
      append(verdict, [h("span", { class: "muted" }, "Click notes above to add them to the cell.")]);
    }

    app.appendChild(h("div", { class: "builder" },
      h("div", { class: "card card-pad" },
        h("div", { class: "toggle-row" }, h("h2", null, "Pattern builder"), progSel),
        h("p", { class: "muted", style: "margin:6px 0 12px;max-width:80ch" },
          "Pick the notes that decorate each principal tone. Everything is shown from C; notes below C are ",
          h("span", { class: "r-I" }, "infrapolations"), ", notes between the principal tones are ",
          h("span", { class: "r-N" }, "interpolations"), ", notes above the next principal tone are ",
          h("span", { class: "r-U" }, "ultrapolations"), ". Order matters: notes are played in the order you add them."),
        h("div", { class: "ruler-wrap" }, ruler), chips, verdict),
      detailBox));
    if (cell.length >= 1) {
      renderDetail(detailBox, { prog: prog, cell: cell, id: rec ? id : null, sectionLabel: null,
        book: rec ? rec.p.book : null, inThesaurus: false });
    }
  }

  function whyOutside(prog, cell) {
    if (E.hasPcRepeat(cell, prog.interval)) return "not in the canonical enumeration: a pitch class repeats within the cell.";
    var w = S.catalog.windows[prog.key];
    var roles = E.rolesOf(cell, prog.interval);
    var mixed = roles.some(function (r) { return r !== roles[0]; });
    for (var i = 1; i < cell.length; i++) {
      var r = roles[i - 1];
      var dist = r === "I" ? -cell[i] : r === "U" ? cell[i] - prog.interval : 0;
      var lim = r === "I" ? (mixed ? w.mixedInfra : w.single) : (mixed ? w.mixedUltra : w.single);
      if (r !== "N" && dist > lim) return "not in the canonical enumeration: " + ROLE_NAME[r] + " reaches " + dist +
        " semitones out (the window is " + lim + ").";
    }
    if (!mixed && roles[0] !== "N" && roles.length > 1) return "not in the canonical enumeration: its zig-zag contour is only generated under the ‘any contour’ rules.";
    if (mixed && roles.length > 3) return "not in the canonical enumeration: mixed sections use one note per role.";
    if (!mixed && roles.length > 3) return "not in the canonical enumeration: sections stop at three added notes.";
    if (!mixed && roles[0] === "N") return "not in the canonical enumeration: interpolations are listed in ascending order.";
    return "not in the canonical enumeration (its section is not generated).";
  }

  // ------------------------------------------------------------- research
  function renderResearch() {
    var any = S.researchContour === "any";
    var fits = any ? S.catalog.fitAnyContour : S.catalog.fit;
    var sum = any ? S.catalog.fitAnyContourSummary : S.catalog.fitSummary;
    var anchors = S.catalog.anchors;

    var stats = h("div", { class: "stats" },
      stat(sum.multiAnchorInOrder + " / " + sum.multiAnchorSections, "sections with 2+ anchors appear in the enumeration's order"),
      stat(sum.anchorsReproducedExactly, "anchors whose book number is reproduced exactly"),
      stat(sum.predictedNumbers, "book numbers predicted in exactly-fitting sections"),
      stat(sum.conflicts, "anchors that contradict their section (listed on the cards)"),
      stat(anchors.length, "published anchors (number ↔ pattern facts)"));

    var intro = h("div", { class: "card card-pad prose" },
      h("h2", null, "Is there an algorithm behind the Thesaurus?"),
      h("p", null, "Slonimsky never published a procedure, but his numbering leaves fingerprints. Each ",
        h("em", null, "anchor"), " below ties a known book number to the pitches of its cell (mostly from the twelve-tone rows ",
        "Gotham & Yust catalogued). The reconstruction places every anchor in its own canonical enumeration and asks two questions: ",
        "does the book list patterns in the same order, and does it list ", h("em", null, "all"), " of them?"),
      h("p", null, h("span", { class: "pill exact" }, "exact"), " sections match number for number: the book is the complete enumeration there, so the numbers in between can be predicted. ",
        h("span", { class: "pill selection" }, "in order"), " sections keep the enumeration's order but skip patterns: the book is a selection from the same space. ",
        "No section with two or more anchors contradicts the enumeration's order. A few anchors (✗) don't fit their section at all; ",
        "they are shown, not hidden, and a section with one makes no predictions."),
      h("div", { class: "toggle-row" }, h("span", { class: "eyebrow" }, "Rules for multi-note infra/ultrapolation"),
        (function () {
          var box = h("div", { class: "seg" });
          [["monotone", "Monotone (default)"], ["any", "Any contour, grouped by shape"]].forEach(function (o) {
            box.appendChild(h("button", { type: "button", "aria-pressed": S.researchContour === o[0] ? "true" : "false",
              onclick: function () { S.researchContour = o[0]; render(); } }, o[1]));
          });
          return box;
        })()));

    var grid = h("div", { class: "fit-grid" });
    fits.forEach(function (f) { grid.appendChild(fitCard(f)); });

    var table = h("table", { class: "anchors" },
      h("thead", null, h("tr", null, ["№", "Chapter", "Source heading", "Cell (from C)", "Placed as", "Source"].map(function (t) {
        return h("th", null, t);
      }))));
    var tb = h("tbody");
    var anyPlaced = {};
    S.catalog.fitAnyContour.forEach(function (f) {
      f.anchors.forEach(function (a) { anyPlaced[a.number] = f.label + " #" + a.index; });
    });
    anchors.forEach(function (a) {
      var prog = S.progs[a.progression];
      var placed = a.placed;
      var cellStr = a.cell ? a.cell.map(function (p) { return E.pcName(p, sharpsFor(prog)); }).join(" ") : "—";
      var where;
      if (placed) {
        var sec = sectionOf(prog, placed.section);
        where = h("a", { href: patternHash(placed.id) }, (sec ? sec.label : placed.section) + " #" + placed.index);
        if (placed.relabelled) where = h("span", null, where, h("span", { class: "muted" }, " (moved from source heading)"));
      } else {
        where = h("span", { class: "muted" }, !a.cell ? "label only"
          : anyPlaced[a.number] ? "only under ‘any contour’: " + anyPlaced[a.number]
          : "outside the reconstruction");
      }
      tb.appendChild(h("tr", null, h("td", { class: "num" }, a.number), h("td", null, prog.name),
        h("td", null, a.label || "—"), h("td", { class: "mono" }, cellStr), h("td", null, where),
        h("td", { class: "muted", style: "font-size:12.5px" }, a.source + (a.note ? " (" + a.note + ")" : ""))));
    });
    table.appendChild(tb);

    var help = h("div", { class: "card card-pad prose" },
      h("h3", null, "What would settle the remaining questions"),
      h("p", null, "The anchors are biased: most come from patterns that happen to be twelve-tone rows. A few pages of the book transcribed as ",
        h("code", null, "number, chapter, heading, notes of the first cell"),
        " (for example the Tritone chapter, #1–180) would show exactly which patterns Slonimsky skipped in the ‘in order’ sections, ",
        "and whether the skips follow a rule. Add rows to ", h("code", null, "src/slonimsky/data/anchors.csv"),
        " and run ", h("code", null, "slonimsky fit"), "."));

    app.appendChild(h("div", { class: "research" }, intro, stats, grid,
      h("div", { class: "card" }, h("div", { class: "card-pad" }, h("h3", null, "All anchors")), h("div", { class: "table-wrap" }, table)),
      help));
  }

  function stat(num, label) {
    return h("div", { class: "card stat" }, h("div", { class: "num" }, String(num)), h("div", { class: "lbl" }, label));
  }

  function fitCard(f) {
    var prog = S.progs[f.progression];
    var nums = f.anchors.map(function (a) { return a.number; });
    var W = 320, H = 66, pad = 14;
    var bookLo = Math.min.apply(null, nums), bookHi = Math.max.apply(null, nums);
    if (f.verdict === "exact") { bookLo = f.offset + 1; bookHi = f.offset + f.size; }
    var bookSpan = Math.max(1, bookHi - bookLo);
    var svg = s("svg", { viewBox: "0 0 " + W + " " + H, role: "img",
      "aria-label": "Book numbers (top) linked to positions in the canonical section (bottom)" });
    svg.appendChild(s("line", { class: "axis", x1: pad, x2: W - pad, y1: 16, y2: 16 }));
    svg.appendChild(s("line", { class: "axis", x1: pad, x2: W - pad, y1: H - 16, y2: H - 16 }));
    var bx = function (n) { return pad + ((n - bookLo) / bookSpan) * (W - 2 * pad); };
    var ix = function (i) { return pad + ((i - 1) / Math.max(1, f.size - 1)) * (W - 2 * pad); };
    if (f.anchors.length === 1) bx = function () { return ix(f.anchors[0].index); };
    f.anchors.forEach(function (a) {
      svg.appendChild(s("line", { class: "link " + f.verdict, x1: bx(a.number), y1: 16, x2: ix(a.index), y2: H - 16 }));
      svg.appendChild(s("circle", { cx: bx(a.number), cy: 16, r: 3, fill: "var(--accent)" }));
      svg.appendChild(s("circle", { cx: ix(a.index), cy: H - 16, r: 3, fill: "var(--ink-3)" }));
    });
    svg.appendChild(s("text", { class: "fl-book", x: pad, y: 10 }, "book №" + bookLo + (bookHi > bookLo ? "–" + bookHi : "")));
    svg.appendChild(s("text", { class: "fl-idx", x: pad, y: H - 3 }, "canonical #1–" + f.size));
    var list = h("div", { style: "font-size:12.5px;margin-top:4px;display:flex;flex-wrap:wrap;gap:4px 10px" });
    f.anchors.forEach(function (a) {
      list.appendChild(h("a", { href: patternHash(a.id), title: cellText(prog, a.cell) },
        "№" + a.number + " → #" + a.index + (a.relabelled ? "*" : "")));
    });
    (f.conflicts || []).forEach(function (a) {
      list.appendChild(h("span", { class: "r-I", title: "pitch classes " + a.cell.join(" ") + " are not in this section's enumeration" },
        "№" + a.number + " ✗"));
    });
    var extra = f.verdict === "exact" ? "predicts №" + (f.offset + 1) + "–" + (f.offset + f.size) : f.size + " in the enumeration";
    return h("div", { class: "card fitcard" },
      h("h3", null, h("span", null, f.label), h("span", { class: "pill " + f.verdict }, VERDICT_TEXT[f.verdict] || f.verdict)),
      h("div", { class: "sub" }, prog.title + " · " + extra),
      svg, list);
  }

  // ---------------------------------------------------------------- about
  function renderAbout() {
    app.appendChild(h("div", { class: "card card-pad prose", style: "margin:0 auto" },
      h("h2", null, "About this lab"),
      h("p", null, "Nicolas Slonimsky's ", h("em", null, "Thesaurus of Scales and Melodic Patterns"),
        " (1947) builds most of its 1,330 patterns from one idea: divide one or more octaves into equal parts (the ",
        h("em", null, "principal tones"), ") and decorate every principal tone with the same small figure. ",
        "The figure's added notes are named by where they fall:"),
      h("ul", null,
        h("li", null, h("b", { class: "r-N" }, "Interpolation"), ": between the principal tones;"),
        h("li", null, h("b", { class: "r-I" }, "Infrapolation"), ": below the current principal tone;"),
        h("li", null, h("b", { class: "r-U" }, "Ultrapolation"), ": above the next principal tone;"),
        h("li", null, "and their combinations, named in playing order: Infra-Interpolation, Inter-Ultrapolation, Infra-Ultrapolation, Infra-Inter-Ultrapolation…")),
      h("p", null, "The twelve chapters are the twelve equal divisions: tritone (1 octave ÷ 2), ditone (÷ 3), sesquitone (÷ 4), whole-tone (÷ 6), ",
        "semitone (÷ 12), then the multi-octave cycles: quadritone (2 ÷ 3), sesquiquadritone (3 ÷ 4), quinquetone (5 ÷ 6), ",
        "diatessaron (5 ÷ 12), septitone (7 ÷ 6), diapente (7 ÷ 12) and sesquiquinquetone (11 ÷ 12)."),
      h("h3", null, "What is reconstructed"),
      h("p", null, "The Thesaurus tab lists every pattern the reconstructed rules generate, in canonical order: ",
        S.catalog.total + " patterns, about 2.7 times the book's progression chapters. Where the fit to published pattern numbers is exact, ",
        "patterns carry their book number (solid: confirmed by a source; dashed: predicted). The Research tab shows the evidence."),
      h("p", null, "This is an independent study tool, not a copy of the book: no pages or notation from the Thesaurus are reproduced. ",
        "If you use these patterns, the book itself is worth owning."),
      h("h3", null, "Keyboard"),
      h("p", null, h("code", null, "Space"), " play/stop · ", h("code", null, "← →"), " previous/next pattern · ",
        h("code", null, "R"), " random · ", h("code", null, "L"), " mark learned"),
      h("h3", null, "Credits"),
      h("p", null, "Anchors: Mark Gotham & Jason Yust, ", h("em", null, "Serial Analysis"), " (DLfM 2021) and its open anthology of rows; ",
        "J. Bair (2003) for #286. Notation rendered with abcjs (MIT). Catalog v" + S.catalog.version + ", generated " + S.catalog.generated + ".")));
  }

  // ------------------------------------------------------------ keyboard
  document.addEventListener("keydown", function (e) {
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "select" || tag === "textarea" || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === " ") {
      e.preventDefault();
      togglePlay();
    } else if (S.view === "thesaurus" && (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === "j")) {
      e.preventDefault();
      step(1);
    } else if (S.view === "thesaurus" && (e.key === "ArrowLeft" || e.key === "ArrowUp" || e.key === "k")) {
      e.preventDefault();
      step(-1);
    } else if (S.view === "thesaurus" && e.key.toLowerCase() === "r") {
      randomPattern();
    } else if (S.view === "thesaurus" && e.key.toLowerCase() === "l") {
      toggleLearned();
    }
  });

  // --------------------------------------------------------------- theme
  function applyTheme(t) {
    if (t) document.documentElement.setAttribute("data-theme", t);
  }
  applyTheme(store("theme", "")); // only a choice made here; otherwise keep the host's theme
  document.getElementById("theme-toggle").addEventListener("click", function () {
    var cur = document.documentElement.getAttribute("data-theme");
    var dark = cur ? cur === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    var next = dark ? "light" : "dark";
    applyTheme(next);
    save("theme", next);
    render();
  });
  var spellingSel = document.getElementById("spelling");
  spellingSel.value = S.spelling;
  spellingSel.addEventListener("change", function (e) {
    S.spelling = e.target.value;
    save("spelling", S.spelling);
    render();
  });

  // ---------------------------------------------------------------- boot
  function index(catalog) {
    S.catalog = catalog;
    catalog.progressions.forEach(function (p) {
      S.progs[p.key] = p;
      p.sections.forEach(function (sec) {
        sec.patterns.forEach(function (pt) { S.patterns[pt.id] = { prog: p, section: sec, p: pt }; });
      });
    });
  }

  function start(catalog) {
    index(catalog);
    window.addEventListener("hashchange", function () {
      if (location.hash !== currentHash) { parseHash(); render(); }
    });
    parseHash();
    render();
  }

  if (window.SLONIMSKY_CATALOG) {
    start(window.SLONIMSKY_CATALOG);
  } else {
    fetch("data/catalog.json")
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(start)
      .catch(function (err) {
        app.innerHTML = "";
        app.appendChild(h("div", { class: "card card-pad" }, h("h2", null, "Couldn't load the catalog"),
          h("p", null, String(err)), h("p", null, "Run ", h("code", null, "slonimsky serve"), " and open the address it prints.")));
      });
  }
})();
