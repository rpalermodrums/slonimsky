/**
 * Core types for the Slonimsky Pattern Practice Tool
 *
 * Based on Nicolas Slonimsky's "Thesaurus of Scales and Melodic Patterns" (1947)
 * which systematically divides the octave and decorates with interpolations/ultrapolations.
 */

// ============= FUNDAMENTAL TYPES =============

/** Pitch class (0-11, where 0=C, 1=C#/Db, 2=D, etc.) */
export type PitchClass = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;

/** All valid pitch classes */
export const PITCH_CLASSES: readonly PitchClass[] = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
] as const;

/** Pitch class names (sharps) */
export const PITCH_CLASS_NAMES_SHARP: readonly string[] = [
  "C",
  "C#",
  "D",
  "D#",
  "E",
  "F",
  "F#",
  "G",
  "G#",
  "A",
  "A#",
  "B",
] as const;

/** Pitch class names (flats) */
export const PITCH_CLASS_NAMES_FLAT: readonly string[] = [
  "C",
  "Db",
  "D",
  "Eb",
  "E",
  "F",
  "Gb",
  "G",
  "Ab",
  "A",
  "Bb",
  "B",
] as const;

// ============= OCTAVE DIVISIONS =============

/**
 * How the octave is divided into equal parts.
 * This is the foundation of Slonimsky's system.
 *
 * - 2: Tritone progression (C-F#-C) - 6 semitones apart
 * - 3: Ditone progression (C-E-G#-C) - 4 semitones apart (augmented triad)
 * - 4: Sesquitone progression (C-Eb-F#-A-C) - 3 semitones apart (diminished 7th)
 * - 6: Whole-tone progression (C-D-E-F#-G#-A#-C) - 2 semitones apart
 * - 12: Chromatic progression - 1 semitone apart
 */
export type OctaveDivision = 2 | 3 | 4 | 6 | 12;

/** Human-readable names for divisions */
export const DIVISION_NAMES: Record<OctaveDivision, string> = {
  2: "Tritone",
  3: "Ditone",
  4: "Sesquitone",
  6: "Whole-Tone",
  12: "Chromatic",
} as const;

/** Interval in semitones for each division */
export const DIVISION_INTERVALS: Record<OctaveDivision, number> = {
  2: 6, // Tritone
  3: 4, // Major third
  4: 3, // Minor third
  6: 2, // Whole step
  12: 1, // Half step
} as const;

// ============= INTERPOLATION =============

/**
 * Interpolation adds notes BETWEEN principal tones.
 *
 * - none: No interpolation (just the skeleton)
 * - ascending: Fill from below (C → D → E → F#)
 * - descending: Fill from above (C → B → A → G → F#)
 * - alternating: Mixed directions
 */
export type InterpolationType = "none" | "ascending" | "descending" | "alternating";

/** Configuration for interpolation */
export interface InterpolationConfig {
  /** Type of interpolation */
  type: InterpolationType;
  /** Number of notes to add between each pair of principal tones */
  count: number;
  /** Custom interval pattern for 'alternating' type (in semitones) */
  customIntervals?: number[];
}

// ============= ULTRAPOLATION =============

/**
 * Ultrapolation adds notes BEYOND principal tones (overshoot then return).
 *
 * - none: No ultrapolation
 * - above: Overshoot upward, then return (C → D → C# for target C#)
 * - below: Undershoot downward, then return
 * - both: Both directions
 */
export type UltrapolationType = "none" | "above" | "below" | "both";

/** Configuration for ultrapolation */
export interface UltrapolationConfig {
  /** Type of ultrapolation */
  type: UltrapolationType;
  /** How many semitones to overshoot */
  semitones: number;
}

// ============= PATTERN =============

/** Pattern category matching book organization */
export type PatternCategory =
  | "tritone-progression"
  | "ditone-progression"
  | "sesquitone-progression"
  | "whole-tone-progression"
  | "chromatic-progression";

/** Book reference for patterns that map to Slonimsky's original */
export interface BookReference {
  page: number;
  pattern: number;
}

/**
 * A complete Slonimsky pattern definition.
 * Immutable after creation.
 */
export interface SlonimskyPattern {
  /** Unique identifier (e.g., "T2-I2A-U0" = Tritone, 2 ascending interp, no ultra) */
  readonly id: string;

  /** Human-readable name */
  readonly name: string;

  /** Category in the book */
  readonly category: PatternCategory;

  /** How the octave is divided */
  readonly division: OctaveDivision;

  /** Interpolation configuration */
  readonly interpolation: InterpolationConfig;

  /** Ultrapolation configuration */
  readonly ultrapolation: UltrapolationConfig;

  /**
   * The interval sequence in semitones.
   * This is the "DNA" of the pattern - independent of starting note.
   * Positive = ascending, negative = descending.
   */
  readonly intervals: readonly number[];

  /**
   * Pre-computed pitch classes starting from C (0).
   * Useful for quick display without recalculation.
   */
  readonly pitchClasses: readonly PitchClass[];

  /** Reference to original book location (if known) */
  readonly bookRef?: BookReference;

  /** Tags for search/filtering */
  readonly tags: readonly string[];
}

// ============= PLAYBACK =============

/** A single note event for playback/sequencing */
export interface NoteEvent {
  /** MIDI note number (60 = middle C, C4) */
  pitch: number;
  /** Start time in beats (or seconds, depending on context) */
  time: number;
  /** Duration in beats (or seconds) */
  duration: number;
  /** Velocity 0-127 */
  velocity: number;
}

/** Playback state for the transport */
export interface PlaybackState {
  /** Is audio currently playing? */
  isPlaying: boolean;
  /** Tempo in BPM */
  tempo: number;
  /** Current beat position */
  currentBeat: number;
  /** Loop playback? */
  loop: boolean;
  /** Root MIDI note to start pattern on (default: 60 = C4) */
  rootNote: number;
  /** How many octaves to span (1-4) */
  octaveSpan: number;
  /** Note duration as fraction of beat (e.g., 0.5 = eighth notes at tempo) */
  noteDuration: number;
}

/** Default playback state */
export const DEFAULT_PLAYBACK_STATE: PlaybackState = {
  isPlaying: false,
  tempo: 120,
  currentBeat: 0,
  loop: true,
  rootNote: 60, // C4
  octaveSpan: 1,
  noteDuration: 0.5,
} as const;

// ============= MELODIC GRAPH =============

/** A node in the melodic graph */
export interface MelodicGraphNode {
  /** The pitch class this node represents */
  pitchClass: PitchClass;
  /** IDs of patterns that include this pitch class */
  patternIds: readonly string[];
}

/** An edge in the melodic graph */
export interface MelodicGraphEdge {
  /** Source pitch class */
  from: PitchClass;
  /** Target pitch class */
  to: PitchClass;
  /** Interval in semitones (can be negative) */
  interval: number;
  /** Weight for pathfinding (higher = preferred) */
  weight: number;
  /** IDs of patterns that use this transition */
  patternIds: readonly string[];
}

/** The complete melodic graph structure */
export interface MelodicGraph {
  /** All nodes indexed by pitch class */
  nodes: Map<PitchClass, MelodicGraphNode>;
  /** All edges */
  edges: readonly MelodicGraphEdge[];
}

// ============= UI STATE =============

/** Filter options for pattern browsing */
export interface PatternFilters {
  /** Filter by division type */
  division?: OctaveDivision;
  /** Filter by interpolation type */
  interpolationType?: InterpolationType;
  /** Filter by ultrapolation type */
  ultrapolationType?: UltrapolationType;
  /** Search query */
  searchQuery?: string;
}

/** User settings/preferences */
export interface UserSettings {
  /** Use sharps or flats for display */
  useFlats: boolean;
  /** Default tempo */
  defaultTempo: number;
  /** Default root note */
  defaultRootNote: number;
  /** Show book references */
  showBookRefs: boolean;
}

/** Default user settings */
export const DEFAULT_USER_SETTINGS: UserSettings = {
  useFlats: false,
  defaultTempo: 120,
  defaultRootNote: 60,
  showBookRefs: true,
} as const;
