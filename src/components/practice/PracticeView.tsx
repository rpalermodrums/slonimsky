import { X, Play, Pause, RotateCcw, ChevronUp, ChevronDown } from "lucide-react";
import { usePlaybackStore } from "@/stores/playbackStore";
import { usePatternStore } from "@/stores/patternStore";
import { PianoKeyboard } from "@/components/piano/PianoKeyboard";
import { PatternVisualization } from "@/components/pattern/PatternVisualization";
import { cn } from "@/lib/utils";
import { useMemo, useState, useEffect, useCallback, useRef } from "react";
import { pitchClassesToMidi } from "@/core";

interface PracticeViewProps {
  onClose: () => void;
}

export function PracticeView({ onClose }: PracticeViewProps) {
  const {
    isPlaying,
    isInitialized,
    tempo,
    rootNote,
    octaves,
    currentNote,
    currentNoteIndex,
    practiceMode,
    initialize,
    play,
    stop,
    setTempo,
    setPracticeMode,
  } = usePlaybackStore();

  const { selectedPattern } = usePatternStore();

  const [countIn, setCountIn] = useState<number | null>(null);

  const patternNotes = useMemo(() => {
    if (!selectedPattern) return [];
    const notes: number[] = [];
    for (let o = 0; o < octaves; o++) {
      const octaveNotes = pitchClassesToMidi(
        selectedPattern.pitchClasses,
        rootNote + o * 12,
        selectedPattern.intervals
      );
      notes.push(...octaveNotes);
    }
    return notes;
  }, [selectedPattern, rootNote, octaves]);

  const startPlayback = useCallback(async () => {
    if (!selectedPattern) return;
    if (!isInitialized) {
      await initialize();
    }
    play(selectedPattern);
  }, [selectedPattern, isInitialized, initialize, play]);

  const pendingPlaybackRef = useRef(false);

  useEffect(() => {
    if (countIn === null) {
      if (pendingPlaybackRef.current) {
        pendingPlaybackRef.current = false;
        startPlayback();
      }
      return;
    }

    const beatDuration = (60 / tempo) * 1000;
    const timer = setTimeout(() => {
      if (countIn <= 1) {
        pendingPlaybackRef.current = true;
      }
      setCountIn(countIn - 1 > 0 ? countIn - 1 : null);
    }, beatDuration);

    return () => clearTimeout(timer);
  }, [countIn, tempo, startPlayback]);

  const handlePlayPause = async () => {
    if (!selectedPattern) return;

    if (isPlaying) {
      stop();
    } else if (countIn !== null) {
      setCountIn(null);
    } else {
      setCountIn(4);
    }
  };

  const handleReset = () => {
    stop();
    setPracticeMode({
      ...practiceMode,
      currentLoopCount: 0,
    });
    setTempo(practiceMode.startTempo);
  };

  const tempoProgress =
    ((tempo - practiceMode.startTempo) / (practiceMode.endTempo - practiceMode.startTempo)) * 100;

  if (!selectedPattern) {
    return (
      <div className="fixed inset-0 z-50 bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-zinc-400 text-lg">Select a pattern to practice</p>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-zinc-800 text-zinc-300 rounded-lg hover:bg-zinc-700 transition-micro"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-zinc-950 flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
        <div>
          <h1 className="text-display text-zinc-100">{selectedPattern.name}</h1>
          <p className="text-mono text-zinc-500 mt-1">{selectedPattern.id}</p>
        </div>

        <button
          onClick={onClose}
          className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 transition-micro"
        >
          <X className="w-5 h-5" />
        </button>
      </header>

      <div className="flex-1 flex flex-col p-6 gap-6 overflow-hidden">
        <div className="flex-1 bg-zinc-900/50 rounded-xl border border-zinc-800 p-6 flex items-center justify-center">
          <PatternVisualization
            pattern={selectedPattern}
            rootNote={rootNote}
            currentNoteIndex={isPlaying ? (currentNoteIndex ?? undefined) : undefined}
            height={280}
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="bg-zinc-900/50 rounded-xl border border-zinc-800 p-4">
            <div className="text-label mb-2">Current Tempo</div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setTempo(Math.max(40, tempo - 5))}
                className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 transition-micro"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
              <span className="text-3xl font-bold text-amber-400 tabular-nums min-w-[80px] text-center">
                {tempo}
              </span>
              <button
                onClick={() => setTempo(Math.min(240, tempo + 5))}
                className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 transition-micro"
              >
                <ChevronUp className="w-4 h-4" />
              </button>
              <span className="text-zinc-500 text-sm">BPM</span>
            </div>
          </div>

          <div className="bg-zinc-900/50 rounded-xl border border-zinc-800 p-4">
            <div className="text-label mb-2">Loop Progress</div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-green-400 tabular-nums">
                {practiceMode.currentLoopCount}
              </span>
              <span className="text-zinc-500">/ {practiceMode.loopsPerTempo}</span>
            </div>
            <div className="mt-2 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all duration-300"
                style={{
                  width: `${(practiceMode.currentLoopCount / practiceMode.loopsPerTempo) * 100}%`,
                }}
              />
            </div>
          </div>

          <div className="bg-zinc-900/50 rounded-xl border border-zinc-800 p-4">
            <div className="text-label mb-2">Tempo Ramp</div>
            <div className="flex items-baseline gap-2">
              <span className="text-zinc-400 tabular-nums">{practiceMode.startTempo}</span>
              <span className="text-zinc-600">→</span>
              <span className="text-amber-400 font-bold tabular-nums">
                {practiceMode.endTempo}
              </span>
              <span className="text-zinc-500 text-sm">BPM</span>
            </div>
            <div className="mt-2 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-300"
                style={{ width: `${Math.max(0, Math.min(100, tempoProgress))}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center gap-6">
          <button
            onClick={handleReset}
            className="p-3 rounded-xl bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 transition-micro"
            title="Reset practice"
          >
            <RotateCcw className="w-5 h-5" />
          </button>

          <div className="relative">
            {(isPlaying || countIn !== null) && (
              <div
                className="absolute inset-0 rounded-full bg-green-500/20"
                style={{
                  animation: `pulse ${60 / tempo}s ease-in-out infinite`,
                }}
              />
            )}
            <button
              onClick={handlePlayPause}
              className={cn(
                "relative w-16 h-16 rounded-full flex items-center justify-center transition-micro",
                isPlaying || countIn !== null
                  ? "bg-green-500 hover:bg-green-400 text-white"
                  : "bg-amber-500 hover:bg-amber-400 text-zinc-900"
              )}
            >
              {isPlaying ? (
                <Pause className="w-7 h-7" />
              ) : countIn !== null ? (
                <span className="text-2xl font-bold">{countIn}</span>
              ) : (
                <Play className="w-7 h-7 ml-1" />
              )}
            </button>
          </div>

          <div
            className={cn(
              "flex gap-1.5 transition-opacity",
              isPlaying ? "opacity-100" : "opacity-30"
            )}
          >
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="w-3 h-3 rounded-full bg-amber-500"
                style={{
                  animation: isPlaying
                    ? `metronome-beat ${(60 / tempo) * 4}s ease-in-out infinite`
                    : "none",
                  animationDelay: `${(60 / tempo) * i}s`,
                  opacity: 0.3,
                }}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-zinc-800 bg-zinc-900/80 px-6 py-3">
        <div className="max-w-4xl mx-auto">
          <PianoKeyboard
            startNote={Math.max(36, rootNote - 12)}
            endNote={Math.min(96, rootNote + 24 + (octaves - 1) * 12)}
            activeNotes={currentNote !== null ? [currentNote] : []}
            highlightedNotes={patternNotes}
          />
        </div>
      </div>
    </div>
  );
}
