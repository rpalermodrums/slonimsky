import { create } from "zustand";
import { audioEngine } from "@/audio";
import type { SlonimskyPattern } from "@/core/types";
import { patternToNoteEvents } from "@/core/pattern";

interface PracticeMode {
  enabled: boolean;
  startTempo: number;
  endTempo: number;
  incrementBpm: number;
  loopsPerTempo: number;
  currentLoopCount: number;
}

interface PlaybackStore {
  isPlaying: boolean;
  isPreviewing: boolean;
  isInitialized: boolean;
  tempo: number;
  rootNote: number;
  octaves: number;
  loop: boolean;
  currentNote: number | null;
  currentNoteIndex: number | null;
  practiceMode: PracticeMode;

  initialize: () => Promise<void>;
  play: (pattern: SlonimskyPattern) => void;
  preview: (pattern: SlonimskyPattern) => void;
  stopPreview: () => void;
  stop: () => void;
  setTempo: (bpm: number) => void;
  setRootNote: (midi: number) => void;
  setOctaves: (count: number) => void;
  setLoop: (enabled: boolean) => void;
  setPracticeMode: (settings: Partial<PracticeMode>) => void;
  togglePracticeMode: () => void;
}

export const usePlaybackStore = create<PlaybackStore>((set, get) => ({
  isPlaying: false,
  isPreviewing: false,
  isInitialized: false,
  tempo: 120,
  rootNote: 60,
  octaves: 1,
  loop: true,
  currentNote: null,
  currentNoteIndex: null,
  practiceMode: {
    enabled: false,
    startTempo: 60,
    endTempo: 180,
    incrementBpm: 10,
    loopsPerTempo: 2,
    currentLoopCount: 0,
  },

  initialize: async () => {
    await audioEngine.initialize();
    audioEngine.setTempo(get().tempo);
    audioEngine.onNoteChange((event) =>
      set({ currentNote: event.midi, currentNoteIndex: event.index })
    );
    set({ isInitialized: true });
  },

  play: (pattern) => {
    const { rootNote, octaves, loop, tempo } = get();

    audioEngine.setTempo(tempo);

    const events = patternToNoteEvents(pattern, {
      rootMidi: rootNote,
      octaves,
      noteDuration: 0.5,
      velocity: 100,
    });

    audioEngine.schedulePattern(events, loop);
    audioEngine.play();
    set({ isPlaying: true, isPreviewing: false });
  },

  preview: (pattern) => {
    const { rootNote, isPlaying } = get();
    if (isPlaying) return;

    const events = patternToNoteEvents(pattern, {
      rootMidi: rootNote,
      octaves: 1,
      noteDuration: 0.25,
      velocity: 80,
    });

    audioEngine.setTempo(180);
    audioEngine.preview(events, 5);
    set({ isPreviewing: true });
  },

  stopPreview: () => {
    const { isPlaying, isPreviewing, tempo } = get();
    if (isPreviewing && !isPlaying) {
      audioEngine.stop();
      audioEngine.setTempo(tempo);
      set({ isPreviewing: false, currentNote: null, currentNoteIndex: null });
    }
  },

  stop: () => {
    audioEngine.stop();
    set({ isPlaying: false, isPreviewing: false, currentNote: null, currentNoteIndex: null });
  },

  setTempo: (bpm) => {
    audioEngine.setTempo(bpm);
    set({ tempo: bpm });
  },

  setRootNote: (midi) => set({ rootNote: midi }),

  setOctaves: (count) => set({ octaves: Math.max(1, Math.min(4, count)) }),

  setLoop: (enabled) => set({ loop: enabled }),

  setPracticeMode: (settings) =>
    set((state) => ({
      practiceMode: { ...state.practiceMode, ...settings },
    })),

  togglePracticeMode: () =>
    set((state) => {
      const newEnabled = !state.practiceMode.enabled;
      if (newEnabled) {
        return {
          practiceMode: {
            ...state.practiceMode,
            enabled: true,
            currentLoopCount: 0,
          },
          tempo: state.practiceMode.startTempo,
        };
      }
      return {
        practiceMode: { ...state.practiceMode, enabled: false },
      };
    }),
}));
