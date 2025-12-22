/**
 * Pattern generation algorithm for Slonimsky patterns.
 *
 * The algorithm:
 * 1. Divide the octave into N equal parts (principal tones)
 * 2. Between each pair of principal tones, add interpolation notes
 * 3. Before/after principal tones, add ultrapolation notes
 * 4. Return the resulting interval sequence
 */

import {
  type InterpolationConfig,
  type InterpolationType,
  type OctaveDivision,
  type PatternCategory,
  type PitchClass,
  type SlonimskyPattern,
  type UltrapolationConfig,
  type UltrapolationType,
  DIVISION_INTERVALS,
  DIVISION_NAMES,
} from "./types";

// ============= PATTERN ID GENERATION =============

/**
 * Generate a unique pattern ID from its configuration.
 * Format: D{division}-I{count}{type[0]}-U{semitones}{type[0]}
 * Example: D2-I2A-U1A = Division 2 (tritone), 2 ascending interpolations, 1 semitone ultrapolation above
 */
export function generatePatternId(
  division: OctaveDivision,
  interpolation: InterpolationConfig,
  ultrapolation: UltrapolationConfig
): string {
  const divPart = `D${division}`;

  const interpTypeChar =
    interpolation.type === "none"
      ? "N"
      : interpolation.type === "ascending"
        ? "A"
        : interpolation.type === "descending"
          ? "D"
          : "X"; // alternating
  const interpPart = `I${interpolation.count}${interpTypeChar}`;

  const ultraTypeChar =
    ultrapolation.type === "none"
      ? "N"
      : ultrapolation.type === "above"
        ? "A"
        : ultrapolation.type === "below"
          ? "B"
          : "X"; // both
  const ultraPart = `U${ultrapolation.semitones}${ultraTypeChar}`;

  return `${divPart}-${interpPart}-${ultraPart}`;
}

/**
 * Generate a human-readable pattern name.
 */
export function generatePatternName(
  division: OctaveDivision,
  interpolation: InterpolationConfig,
  ultrapolation: UltrapolationConfig
): string {
  const parts: string[] = [DIVISION_NAMES[division]];

  if (interpolation.type !== "none" && interpolation.count > 0) {
    const interpDesc =
      interpolation.count === 1 ? "1 note" : `${interpolation.count} notes`;
    parts.push(`${interpDesc} ${interpolation.type}`);
  }

  if (ultrapolation.type !== "none" && ultrapolation.semitones > 0) {
    const ultraDesc =
      ultrapolation.semitones === 1 ? "1 semitone" : `${ultrapolation.semitones} semitones`;
    parts.push(`ultra ${ultrapolation.type} ${ultraDesc}`);
  }

  return parts.join(", ");
}

/**
 * Map division to pattern category.
 */
export function divisionToCategory(division: OctaveDivision): PatternCategory {
  switch (division) {
    case 2:
      return "tritone-progression";
    case 3:
      return "ditone-progression";
    case 4:
      return "sesquitone-progression";
    case 6:
      return "whole-tone-progression";
    case 12:
      return "chromatic-progression";
  }
}

// ============= INTERVAL GENERATION =============

/**
 * Generate the interval sequence for a single segment between two principal tones.
 * A segment goes from one skeleton note to the next.
 */
function generateSegmentIntervals(
  principalInterval: number,
  interpolation: InterpolationConfig,
  ultrapolation: UltrapolationConfig
): number[] {
  const intervals: number[] = [];

  // Ultrapolation BEFORE (below = go down first, then up to target)
  if (ultrapolation.type === "below" || ultrapolation.type === "both") {
    intervals.push(-ultrapolation.semitones); // Go down
    intervals.push(ultrapolation.semitones); // Return to start position
  }

  // Interpolation between principal tones
  if (interpolation.type !== "none" && interpolation.count > 0) {
    // Calculate the step size for interpolation
    // We need to fit `count` intermediate notes, so we have (count + 1) steps
    const stepSize = principalInterval / (interpolation.count + 1);

    if (interpolation.type === "ascending") {
      // Ascend step by step to the target
      for (let i = 0; i <= interpolation.count; i++) {
        intervals.push(stepSize);
      }
    } else if (interpolation.type === "descending") {
      // Jump PAST the target, then descend TO it
      const overshoot = stepSize * interpolation.count;
      intervals.push(principalInterval + overshoot);
      for (let i = 0; i < interpolation.count; i++) {
        intervals.push(-stepSize);
      }
    } else if (interpolation.type === "alternating") {
      // Use custom intervals if provided, otherwise default to zigzag
      if (interpolation.customIntervals && interpolation.customIntervals.length > 0) {
        intervals.push(...interpolation.customIntervals);
      } else {
        // Default alternating: up-down-up pattern
        let remaining = principalInterval;
        const halfStep = principalInterval / (interpolation.count + 1);
        for (let i = 0; i <= interpolation.count; i++) {
          if (i % 2 === 0) {
            intervals.push(halfStep * 1.5);
            remaining -= halfStep * 1.5;
          } else {
            intervals.push(-halfStep * 0.5);
            remaining += halfStep * 0.5;
          }
        }
        // Adjust last interval to land on target
        if (intervals.length > 0) {
          intervals[intervals.length - 1] += remaining;
        }
      }
    }
  } else {
    // No interpolation: direct jump to next principal tone
    intervals.push(principalInterval);
  }

  // Ultrapolation AFTER (above = overshoot up, then return down to target)
  if (ultrapolation.type === "above" || ultrapolation.type === "both") {
    intervals.push(ultrapolation.semitones); // Overshoot up
    intervals.push(-ultrapolation.semitones); // Return to target
  }

  return intervals;
}

/**
 * Generate the complete interval sequence for a Slonimsky pattern.
 */
export function generatePatternIntervals(
  division: OctaveDivision,
  interpolation: InterpolationConfig,
  ultrapolation: UltrapolationConfig
): number[] {
  const principalInterval = DIVISION_INTERVALS[division];
  const segmentIntervals = generateSegmentIntervals(
    principalInterval,
    interpolation,
    ultrapolation
  );

  // Repeat the segment for each division of the octave
  const fullPattern: number[] = [];
  for (let d = 0; d < division; d++) {
    fullPattern.push(...segmentIntervals);
  }

  return fullPattern;
}

// ============= PITCH CLASS CONVERSION =============

/**
 * Convert an interval sequence to pitch classes starting from a root.
 */
export function intervalsToPitchClasses(
  intervals: readonly number[],
  root: PitchClass = 0
): PitchClass[] {
  const result: PitchClass[] = [root];
  let current = root;

  for (const interval of intervals) {
    current = (((current + interval) % 12) + 12) % 12;
    result.push(current as PitchClass);
  }

  return result;
}

/**
 * Convert pitch classes to MIDI note numbers starting from a root MIDI note.
 * Uses intervals to accurately track octave position (handles ascending, descending, and mixed patterns).
 */
export function pitchClassesToMidi(
  pitchClasses: readonly PitchClass[],
  rootMidi: number = 60,
  intervals?: readonly number[]
): number[] {
  if (pitchClasses.length === 0) return [];

  const result: number[] = [rootMidi];

  if (intervals && intervals.length === pitchClasses.length - 1) {
    let currentMidi = rootMidi;
    for (const interval of intervals) {
      currentMidi += interval;
      result.push(currentMidi);
    }
  } else {
    let currentMidi = rootMidi;
    for (let i = 1; i < pitchClasses.length; i++) {
      const prevPc = pitchClasses[i - 1];
      const currPc = pitchClasses[i];
      let interval = currPc - prevPc;
      if (interval <= -6) interval += 12;
      else if (interval > 6) interval -= 12;
      currentMidi += interval;
      result.push(currentMidi);
    }
  }

  return result;
}

// ============= TAG GENERATION =============

/**
 * Generate searchable tags for a pattern.
 */
function generateTags(
  division: OctaveDivision,
  interpolation: InterpolationConfig,
  ultrapolation: UltrapolationConfig,
  intervals: readonly number[]
): string[] {
  const tags: string[] = [];

  // Division tags
  tags.push(DIVISION_NAMES[division].toLowerCase());
  tags.push(`division-${division}`);

  // Interpolation tags
  if (interpolation.type !== "none") {
    tags.push(`interp-${interpolation.type}`);
    tags.push(`interp-${interpolation.count}`);
  } else {
    tags.push("no-interpolation");
  }

  // Ultrapolation tags
  if (ultrapolation.type !== "none") {
    tags.push(`ultra-${ultrapolation.type}`);
    tags.push(`ultra-${ultrapolation.semitones}`);
  } else {
    tags.push("no-ultrapolation");
  }

  // Interval content tags
  const uniqueIntervals = [...new Set(intervals.map(Math.abs))];
  for (const interval of uniqueIntervals) {
    tags.push(`interval-${interval}`);
  }

  // Special pattern tags
  if (intervals.every((i) => i > 0)) {
    tags.push("ascending");
  } else if (intervals.every((i) => i < 0)) {
    tags.push("descending");
  } else {
    tags.push("mixed-direction");
  }

  return tags;
}

// ============= PATTERN CREATION =============

/**
 * Create a complete SlonimskyPattern from configuration.
 */
export function createPattern(
  division: OctaveDivision,
  interpolation: InterpolationConfig,
  ultrapolation: UltrapolationConfig
): SlonimskyPattern {
  const intervals = generatePatternIntervals(division, interpolation, ultrapolation);
  const pitchClasses = intervalsToPitchClasses(intervals, 0);

  return {
    id: generatePatternId(division, interpolation, ultrapolation),
    name: generatePatternName(division, interpolation, ultrapolation),
    category: divisionToCategory(division),
    division,
    interpolation,
    ultrapolation,
    intervals,
    pitchClasses,
    tags: generateTags(division, interpolation, ultrapolation, intervals),
  };
}

// ============= CATALOG GENERATION =============

/**
 * Generate all valid pattern combinations for a catalog.
 */
export function generateCatalog(): SlonimskyPattern[] {
  const catalog: SlonimskyPattern[] = [];

  const divisions: OctaveDivision[] = [2, 3, 4, 6, 12];
  const interpolationTypes: InterpolationType[] = ["none", "ascending", "descending", "alternating"];
  const interpolationCounts = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
  const ultrapolationTypes: UltrapolationType[] = ["none", "above", "below", "both"];
  const ultrapolationSemitones = [0, 1, 2, 3];

  for (const division of divisions) {
    for (const interpType of interpolationTypes) {
      for (const interpCount of interpolationCounts) {
        // Skip invalid combinations
        if (interpType === "none" && interpCount > 0) continue;
        if (interpType !== "none" && interpCount === 0) continue;

        // Skip if interpolation count doesn't make sense for division
        // (can't have more interpolation notes than the interval allows)
        const maxInterpCount = DIVISION_INTERVALS[division] - 1;
        if (interpCount > maxInterpCount) continue;

        for (const ultraType of ultrapolationTypes) {
          for (const ultraSemitones of ultrapolationSemitones) {
            // Skip invalid combinations
            if (ultraType === "none" && ultraSemitones > 0) continue;
            if (ultraType !== "none" && ultraSemitones === 0) continue;

            const interpolation: InterpolationConfig = {
              type: interpType,
              count: interpCount,
            };

            const ultrapolation: UltrapolationConfig = {
              type: ultraType,
              semitones: ultraSemitones,
            };

            catalog.push(createPattern(division, interpolation, ultrapolation));
          }
        }
      }
    }
  }

  return catalog;
}

// ============= NOTE EVENT CONVERSION =============

import type { NoteEvent } from "./types";

interface NoteEventOptions {
  rootMidi?: number;
  octaves?: number;
  noteDuration?: number;
  velocity?: number;
}

export function patternToNoteEvents(
  pattern: SlonimskyPattern,
  options: NoteEventOptions = {}
): NoteEvent[] {
  const {
    rootMidi = 60,
    octaves = 1,
    noteDuration = 0.5,
    velocity = 80,
  } = options;

  const events: NoteEvent[] = [];
  let time = 0;

  for (let octave = 0; octave < octaves; octave++) {
    const octaveOffset = octave * 12;
    const midiNotes = pitchClassesToMidi(
      pattern.pitchClasses,
      rootMidi + octaveOffset,
      pattern.intervals
    );

    for (const pitch of midiNotes) {
      events.push({
        pitch,
        time,
        duration: noteDuration * 0.9,
        velocity,
      });
      time += noteDuration;
    }
  }

  return events;
}

// ============= EXPORTS =============

export { type SlonimskyPattern };
