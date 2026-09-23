/*
 * Audio: a small WebAudio synth with a look-ahead scheduler, a metronome
 * click, and a MIDI file writer for downloads. No samples, no network.
 */
(function (root) {
  "use strict";

  function midiToHz(m) {
    return 440 * Math.pow(2, (m - 69) / 12);
  }

  function Player() {
    this.ctx = null;
    this.master = null;
    this.timer = null;
    this.playing = false;
    this.volume = 0.8;
  }

  Player.prototype._ensure = function () {
    if (!this.ctx) {
      var AC = root.AudioContext || root.webkitAudioContext;
      this.ctx = new AC();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      var comp = this.ctx.createDynamicsCompressor();
      this.master.connect(comp);
      comp.connect(this.ctx.destination);
    }
    if (this.ctx.state === "suspended") this.ctx.resume();
    return this.ctx;
  };

  Player.prototype.setVolume = function (v) {
    this.volume = v;
    if (this.master) this.master.gain.value = v;
  };

  // A soft, slightly percussive "felt piano" voice: two detuned partials
  // through a low-pass filter whose cutoff falls with the envelope.
  Player.prototype._voice = function (midi, t, dur, accent) {
    var ctx = this.ctx;
    var f = midiToHz(midi);
    var peak = (accent ? 0.34 : 0.24) * Math.min(1, 1.25 - (midi - 48) / 120);
    var env = ctx.createGain();
    env.gain.setValueAtTime(0.0001, t);
    env.gain.exponentialRampToValueAtTime(peak, t + 0.008);
    env.gain.exponentialRampToValueAtTime(peak * 0.35, t + Math.min(0.25, dur));
    env.gain.setValueAtTime(peak * 0.35, t + dur);
    env.gain.exponentialRampToValueAtTime(0.0001, t + dur + 0.18);
    var lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.setValueAtTime(Math.min(12000, f * 10), t);
    lp.frequency.exponentialRampToValueAtTime(Math.max(400, f * 2.5), t + dur + 0.15);
    lp.connect(env);
    env.connect(this.master);
    [["triangle", 1, 0], ["sine", 2, 3], ["sine", 1, -4]].forEach(function (spec) {
      var o = ctx.createOscillator();
      var g = ctx.createGain();
      o.type = spec[0];
      o.frequency.value = f * spec[1];
      o.detune.value = spec[2];
      g.gain.value = spec[1] === 2 ? 0.18 : 0.5;
      o.connect(g);
      g.connect(lp);
      o.start(t);
      o.stop(t + dur + 0.25);
    });
  };

  Player.prototype._click = function (t, strong) {
    var ctx = this.ctx;
    var o = ctx.createOscillator();
    var g = ctx.createGain();
    o.frequency.value = strong ? 1760 : 1320;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(strong ? 0.25 : 0.12, t + 0.002);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.04);
    o.connect(g);
    g.connect(this.master);
    o.start(t);
    o.stop(t + 0.05);
  };

  /*
   * notes: [{midi, role}], opts: {bpm, perBeat (notes per beat), loop,
   * metronome, onNote(i), onLoop(), onEnd()}
   */
  Player.prototype.play = function (notes, opts) {
    this.stop();
    if (!notes.length) return;
    var ctx = this._ensure();
    var self = this;
    var step = 60 / (opts.bpm || 100) / (opts.perBeat || 2);
    var i = 0;
    var next = ctx.currentTime + 0.06;
    var lookahead = 0.12;
    this.playing = true;
    this._opts = opts;
    function tick() {
      while (self.playing && next < ctx.currentTime + lookahead) {
        if (i >= notes.length) {
          if (opts.loop) {
            i = 0;
            if (opts.onLoop) {
              var fresh = opts.onLoop();
              if (fresh) notes = fresh;
            }
          } else {
            var endAt = next;
            self.playing = false;
            setTimeout(function () { if (opts.onEnd) opts.onEnd(); }, Math.max(0, (endAt - ctx.currentTime) * 1000));
            break;
          }
        }
        var n = notes[i];
        self._voice(n.midi, next, step * 0.92, n.role === "P");
        if (opts.metronome && i % (opts.perBeat || 2) === 0) self._click(next, i === 0);
        (function (idx, when) {
          setTimeout(function () {
            if (self.playing && opts.onNote) opts.onNote(idx);
          }, Math.max(0, (when - ctx.currentTime) * 1000));
        })(i, next);
        i += 1;
        next += step;
      }
    }
    tick();
    this.timer = setInterval(tick, 25);
  };

  Player.prototype.stop = function () {
    this.playing = false;
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  };

  // --------------------------------------------------------------- MIDI
  function vlq(v) {
    var out = [v & 0x7f];
    v >>= 7;
    while (v) {
      out.unshift((v & 0x7f) | 0x80);
      v >>= 7;
    }
    return out;
  }

  function toMidi(notes, bpm, perBeat) {
    var tpq = 480;
    var step = Math.round(tpq / (perBeat || 2));
    var on = Math.max(1, Math.round(step * 0.9));
    var track = [];
    var uspq = Math.round(60000000 / (bpm || 100));
    track.push.apply(track, [0, 0xff, 0x51, 0x03, (uspq >> 16) & 255, (uspq >> 8) & 255, uspq & 255]);
    var pending = 0;
    notes.forEach(function (n) {
      var vel = n.role === "P" ? 104 : 88;
      track.push.apply(track, vlq(pending).concat([0x90, n.midi & 127, vel]));
      track.push.apply(track, vlq(on).concat([0x80, n.midi & 127, 0]));
      pending = step - on;
    });
    track.push.apply(track, vlq(pending).concat([0xff, 0x2f, 0x00]));
    var len = track.length;
    var header = [0x4d, 0x54, 0x68, 0x64, 0, 0, 0, 6, 0, 0, 0, 1, (tpq >> 8) & 255, tpq & 255];
    var trk = [0x4d, 0x54, 0x72, 0x6b, (len >>> 24) & 255, (len >> 16) & 255, (len >> 8) & 255, len & 255];
    return new Uint8Array(header.concat(trk, track));
  }

  root.SlonimskyAudio = { Player: Player, toMidi: toMidi };
})(this);
