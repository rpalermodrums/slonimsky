/**
 * Core music theory module - pure functions, no I/O
 */

// Types
export type {
  PitchClass,
  OctaveDivision,
  InterpolationType,
  InterpolationConfig,
  UltrapolationType,
  UltrapolationConfig,
  PatternCategory,
  BookReference,
  SlonimskyPattern,
  NoteEvent,
  PlaybackState,
  MelodicGraphNode,
  MelodicGraphEdge,
  MelodicGraph,
  PatternFilters,
  UserSettings,
} from "./types";

// Constants
export {
  PITCH_CLASSES,
  PITCH_CLASS_NAMES_SHARP,
  PITCH_CLASS_NAMES_FLAT,
  DIVISION_NAMES,
  DIVISION_INTERVALS,
  DEFAULT_PLAYBACK_STATE,
  DEFAULT_USER_SETTINGS,
} from "./types";

// Pattern generation
export {
  generatePatternId,
  generatePatternName,
  divisionToCategory,
  generatePatternIntervals,
  intervalsToPitchClasses,
  pitchClassesToMidi,
  createPattern,
  generateCatalog,
  patternToNoteEvents,
} from "./pattern";
