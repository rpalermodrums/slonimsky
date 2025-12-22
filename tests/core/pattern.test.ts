import { describe, it, expect } from "vitest";
import {
  createPattern,
  generateCatalog,
  generatePatternId,
  generatePatternIntervals,
  intervalsToPitchClasses,
  pitchClassesToMidi,
} from "../../src/core/pattern";
import type { InterpolationConfig, UltrapolationConfig } from "../../src/core/types";

describe("generatePatternId", () => {
  it("generates correct ID for tritone with no decorations", () => {
    const interp: InterpolationConfig = { type: "none", count: 0 };
    const ultra: UltrapolationConfig = { type: "none", semitones: 0 };
    expect(generatePatternId(2, interp, ultra)).toBe("D2-I0N-U0N");
  });

  it("generates correct ID for ditone with ascending interpolation", () => {
    const interp: InterpolationConfig = { type: "ascending", count: 2 };
    const ultra: UltrapolationConfig = { type: "none", semitones: 0 };
    expect(generatePatternId(3, interp, ultra)).toBe("D3-I2A-U0N");
  });

  it("generates correct ID with ultrapolation", () => {
    const interp: InterpolationConfig = { type: "none", count: 0 };
    const ultra: UltrapolationConfig = { type: "above", semitones: 1 };
    expect(generatePatternId(2, interp, ultra)).toBe("D2-I0N-U1A");
  });
});

describe("generatePatternIntervals", () => {
  it("generates tritone intervals with no decorations", () => {
    const interp: InterpolationConfig = { type: "none", count: 0 };
    const ultra: UltrapolationConfig = { type: "none", semitones: 0 };
    const intervals = generatePatternIntervals(2, interp, ultra);

    // Tritone divides octave in 2: two jumps of 6 semitones
    expect(intervals).toEqual([6, 6]);
  });

  it("generates ditone intervals with no decorations", () => {
    const interp: InterpolationConfig = { type: "none", count: 0 };
    const ultra: UltrapolationConfig = { type: "none", semitones: 0 };
    const intervals = generatePatternIntervals(3, interp, ultra);

    // Ditone divides octave in 3: three jumps of 4 semitones
    expect(intervals).toEqual([4, 4, 4]);
  });

  it("generates sesquitone intervals with no decorations", () => {
    const interp: InterpolationConfig = { type: "none", count: 0 };
    const ultra: UltrapolationConfig = { type: "none", semitones: 0 };
    const intervals = generatePatternIntervals(4, interp, ultra);

    // Sesquitone divides octave in 4: four jumps of 3 semitones
    expect(intervals).toEqual([3, 3, 3, 3]);
  });

  it("generates tritone with 1 ascending interpolation", () => {
    const interp: InterpolationConfig = { type: "ascending", count: 1 };
    const ultra: UltrapolationConfig = { type: "none", semitones: 0 };
    const intervals = generatePatternIntervals(2, interp, ultra);

    // 6 semitones split into 2 steps of 3 each, repeated twice
    expect(intervals).toEqual([3, 3, 3, 3]);
    // Total should equal 12 (one octave)
    expect(intervals.reduce((a, b) => a + b, 0)).toBe(12);
  });

  it("generates pattern with ultrapolation above", () => {
    const interp: InterpolationConfig = { type: "none", count: 0 };
    const ultra: UltrapolationConfig = { type: "above", semitones: 1 };
    const intervals = generatePatternIntervals(2, interp, ultra);

    // Each segment: jump 6, overshoot +1, return -1
    // But wait - the ultrapolation happens after we reach the target
    // So: jump 6, +1, -1, then repeat
    expect(intervals).toEqual([6, 1, -1, 6, 1, -1]);
    // Net should still equal 12
    expect(intervals.reduce((a, b) => a + b, 0)).toBe(12);
  });

  it("generates pattern with ultrapolation below", () => {
    const interp: InterpolationConfig = { type: "none", count: 0 };
    const ultra: UltrapolationConfig = { type: "below", semitones: 1 };
    const intervals = generatePatternIntervals(2, interp, ultra);

    // Each segment: -1 (dip below), +1 (return), then jump 6
    expect(intervals).toEqual([-1, 1, 6, -1, 1, 6]);
    // Net should equal 12
    expect(intervals.reduce((a, b) => a + b, 0)).toBe(12);
  });
});

describe("intervalsToPitchClasses", () => {
  it("converts tritone intervals to pitch classes", () => {
    const intervals = [6, 6];
    const pitchClasses = intervalsToPitchClasses(intervals, 0);

    // Starting at C (0), jump 6 to F# (6), jump 6 to C (0)
    expect(pitchClasses).toEqual([0, 6, 0]);
  });

  it("converts ditone intervals to pitch classes", () => {
    const intervals = [4, 4, 4];
    const pitchClasses = intervalsToPitchClasses(intervals, 0);

    // C -> E -> G# -> C
    expect(pitchClasses).toEqual([0, 4, 8, 0]);
  });

  it("handles different root notes", () => {
    const intervals = [6, 6];
    const pitchClasses = intervalsToPitchClasses(intervals, 2); // Starting on D

    // D (2) -> G# (8) -> D (2)
    expect(pitchClasses).toEqual([2, 8, 2]);
  });

  it("handles negative intervals", () => {
    const intervals = [-1, 1, 6];
    const pitchClasses = intervalsToPitchClasses(intervals, 0);

    // C (0) -> B (11) -> C (0) -> F# (6)
    expect(pitchClasses).toEqual([0, 11, 0, 6]);
  });
});

describe("pitchClassesToMidi", () => {
  it("converts pitch classes to MIDI starting from middle C", () => {
    const pitchClasses = [0, 4, 7] as const;
    const midi = pitchClassesToMidi(pitchClasses, 60);

    // C4 (60), E4 (64), G4 (67)
    expect(midi).toEqual([60, 64, 67]);
  });

  it("handles octave crossings", () => {
    const pitchClasses = [0, 6, 0] as const;
    const midi = pitchClassesToMidi(pitchClasses, 60);

    // C4 (60), F#4 (66), C5 (72) - crossed octave
    expect(midi).toEqual([60, 66, 72]);
  });
});

describe("createPattern", () => {
  it("creates a complete pattern object", () => {
    const interp: InterpolationConfig = { type: "ascending", count: 1 };
    const ultra: UltrapolationConfig = { type: "none", semitones: 0 };
    const pattern = createPattern(2, interp, ultra);

    expect(pattern.id).toBe("D2-I1A-U0N");
    expect(pattern.division).toBe(2);
    expect(pattern.category).toBe("tritone-progression");
    expect(pattern.intervals.length).toBeGreaterThan(0);
    expect(pattern.pitchClasses.length).toBeGreaterThan(0);
    expect(pattern.tags).toContain("tritone");
  });
});

describe("generateCatalog", () => {
  it("generates a non-empty catalog", () => {
    const catalog = generateCatalog();
    expect(catalog.length).toBeGreaterThan(0);
  });

  it("generates unique pattern IDs", () => {
    const catalog = generateCatalog();
    const ids = catalog.map((p) => p.id);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });

  it("includes basic tritone pattern", () => {
    const catalog = generateCatalog();
    const basicTritone = catalog.find((p) => p.id === "D2-I0N-U0N");
    expect(basicTritone).toBeDefined();
    expect(basicTritone?.intervals).toEqual([6, 6]);
  });

  it("all patterns sum to 12 semitones (one octave)", () => {
    const catalog = generateCatalog();
    for (const pattern of catalog) {
      const sum = pattern.intervals.reduce((a, b) => a + b, 0);
      // Use toBeCloseTo for floating point comparison (fractional intervals)
      expect(sum).toBeCloseTo(12, 10);
    }
  });
});
