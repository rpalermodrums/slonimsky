import { create } from "zustand";
import { persist } from "zustand/middleware";
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
  isCountingIn: boolean;
  countInEnabled: boolean;
  countInBeats: number;
  currentCountInBeat: number | null;
  tempo: number;
  rootNote: number;
  octaves: number;
  noteDuration: number;
  direction: "ascending" | "descending";
  loop: boolean;
  currentNote: number | null;
  currentNoteIndex: number | null;
  practiceMode: PracticeMode;
  sessionStats: {
    patternsPlayed: number;
    totalPlayTimeMs: number;
    uniquePatternsCount: number;
  };
  _previewOriginalTempo: number | null;
  _playStartTime: number | null;
  _countInUnsubscribe: (() => void) | null;

  initialize: () => Promise<void>;
  getSessionStats: () => { patternsPlayed: number; totalPlayTimeMs: number; uniquePatternsCount: number };
  resetSessionStats: () => void;
  play: (pattern: SlonimskyPattern) => void;
  setCountInEnabled: (enabled: boolean) => void;
  preview: (pattern: SlonimskyPattern) => void;
  stopPreview: () => void;
  stop: () => void;
  setTempo: (bpm: number) => void;
  setRootNote: (midi: number) => void;
  setOctaves: (count: number) => void;
  setNoteDuration: (duration: number) => void;
  setDirection: (dir: "ascending" | "descending") => void;
  toggleDirection: () => void;
  setLoop: (enabled: boolean) => void;
  setPracticeMode: (settings: Partial<PracticeMode>) => void;
  togglePracticeMode: () => void;
}

export const usePlaybackStore = create<PlaybackStore>()(
  persist(
    (set, get) => ({
  isPlaying: false,
  isPreviewing: false,
  isInitialized: false,
  isCountingIn: false,
  countInEnabled: true,
  countInBeats: 4,
  currentCountInBeat: null,
  tempo: 120,
  rootNote: 60,
  octaves: 1,
  noteDuration: 0.5,
  direction: "ascending" as const,
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
  _previewOriginalTempo: null,
  _playStartTime: null,
  _countInUnsubscribe: null,
  sessionStats: {
    patternsPlayed: 0,
    totalPlayTimeMs: 0,
    uniquePatternsCount: 0,
  },

  getSessionStats: () => {
    const state = get();
    return {
      patternsPlayed: state.sessionStats.patternsPlayed,
      totalPlayTimeMs: state.sessionStats.totalPlayTimeMs,
      uniquePatternsCount: state.sessionStats.uniquePatternsCount,
    };
  },

  resetSessionStats: () => {
    set({
      sessionStats: {
        patternsPlayed: 0,
        totalPlayTimeMs: 0,
        uniquePatternsCount: 0,
      },
    });
  },

  initialize: async () => {
    await audioEngine.initialize();
    audioEngine.setTempo(get().tempo);
    audioEngine.onNoteChange((event) =>
      set({ currentNote: event.midi, currentNoteIndex: event.index })
    );
    audioEngine.onLoopComplete(() => {
      const { practiceMode, tempo } = get();
      if (!practiceMode.enabled) return;

      const newLoopCount = practiceMode.currentLoopCount + 1;

      if (newLoopCount >= practiceMode.loopsPerTempo) {
        const newTempo = tempo + practiceMode.incrementBpm;
        if (newTempo <= practiceMode.endTempo) {
          audioEngine.setTempo(newTempo);
          set({
            tempo: newTempo,
            practiceMode: { ...practiceMode, currentLoopCount: 0 },
          });
        } else {
          audioEngine.stop();
          set({
            isPlaying: false,
            practiceMode: { ...practiceMode, currentLoopCount: 0, enabled: false },
          });
        }
      } else {
        set({
          practiceMode: { ...practiceMode, currentLoopCount: newLoopCount },
        });
      }
    });
    set({ isInitialized: true });
  },

  play: (pattern) => {
    const { rootNote, octaves, noteDuration, direction, loop, tempo, countInEnabled, countInBeats } = get();

    audioEngine.setTempo(tempo);

    let events = patternToNoteEvents(pattern, {
      rootMidi: rootNote,
      octaves,
      noteDuration,
      velocity: 100,
    });

    if (direction === "descending") {
      const pitches = events.map(e => e.pitch).reverse();
      events = events.map((e, i) => ({ ...e, pitch: pitches[i] }));
    }

    if (countInEnabled) {
      audioEngine.schedulePatternWithCountIn(events, loop, countInBeats, (beat) => {
        set({ currentCountInBeat: beat });
      });
      set({ isPlaying: true, isPreviewing: false, isCountingIn: true });
      const prevUnsubscribe = get()._countInUnsubscribe;
      if (prevUnsubscribe) {
        prevUnsubscribe();
      }
      const unsubscribe = audioEngine.onCountInComplete(() => {
        set({ isCountingIn: false, currentCountInBeat: null });
      });
      set({ _countInUnsubscribe: unsubscribe });
    } else {
      audioEngine.schedulePattern(events, loop);
      set({ isPlaying: true, isPreviewing: false });
    }
    audioEngine.play();
  },

  preview: (pattern) => {
    const { rootNote, isPlaying, tempo } = get();
    if (isPlaying) return;

    const events = patternToNoteEvents(pattern, {
      rootMidi: rootNote,
      octaves: 1,
      noteDuration: 0.25,
      velocity: 80,
    });

    audioEngine.setTempo(180);
    audioEngine.preview(events, 5);
    set({ isPreviewing: true, _previewOriginalTempo: tempo });
  },

  stopPreview: () => {
    const { isPlaying, isPreviewing, _previewOriginalTempo } = get();
    if (isPreviewing && !isPlaying) {
      audioEngine.stop();
      if (_previewOriginalTempo !== null) {
        audioEngine.setTempo(_previewOriginalTempo);
      }
      set({ isPreviewing: false, currentNote: null, currentNoteIndex: null, _previewOriginalTempo: null });
    }
  },

  stop: () => {
    audioEngine.stop();
    set({ isPlaying: false, isPreviewing: false, isCountingIn: false, currentNote: null, currentNoteIndex: null, currentCountInBeat: null });
  },

  setCountInEnabled: (enabled) => set({ countInEnabled: enabled }),

  setTempo: (bpm) => {
    audioEngine.setTempo(bpm);
    set({ tempo: bpm });
  },

  setRootNote: (midi) => set({ rootNote: midi }),

  setOctaves: (count) => set({ octaves: Math.max(1, Math.min(4, count)) }),

  setNoteDuration: (duration) => set({ noteDuration: Math.max(0.25, Math.min(1, duration)) }),

  setDirection: (dir) => set({ direction: dir }),

  toggleDirection: () => set((state) => ({ 
    direction: state.direction === "ascending" ? "descending" : "ascending" 
  })),

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
}),
    {
      name: "slonimsky-playback",
      partialize: (state) => ({
        tempo: state.tempo,
        rootNote: state.rootNote,
        octaves: state.octaves,
        noteDuration: state.noteDuration,
        direction: state.direction,
        loop: state.loop,
        countInEnabled: state.countInEnabled,
        practiceMode: {
          startTempo: state.practiceMode.startTempo,
          endTempo: state.practiceMode.endTempo,
          incrementBpm: state.practiceMode.incrementBpm,
          loopsPerTempo: state.practiceMode.loopsPerTempo,
        },
      }),
    }
  )
);
