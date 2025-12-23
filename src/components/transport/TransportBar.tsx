import { Play, Square, RotateCcw, TrendingUp, Music } from "lucide-react";
import { usePlaybackStore } from "@/stores/playbackStore";
import { usePatternStore } from "@/stores/patternStore";
import { cn } from "@/lib/utils";

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

function midiToNoteName(midi: number): string {
  const octave = Math.floor(midi / 12) - 1;
  const note = NOTE_NAMES[midi % 12];
  return `${note}${octave}`;
}

export function TransportBar() {
  const {
    isPlaying,
    isInitialized,
    tempo,
    rootNote,
    octaves,
    loop,
    practiceMode,
    currentNoteIndex,
    initialize,
    play,
    stop,
    setTempo,
    setRootNote,
    setOctaves,
    setLoop,
    togglePracticeMode,
    setPracticeMode,
  } = usePlaybackStore();

  const { selectedPattern } = usePatternStore();

  const handlePlayStop = async () => {
    if (!isInitialized) {
      await initialize();
    }

    if (isPlaying) {
      stop();
    } else if (selectedPattern) {
      play(selectedPattern);
    }
  };

  const totalNotes = selectedPattern ? selectedPattern.intervals.length * octaves : 0;
  const progressPercent =
    isPlaying && currentNoteIndex !== null && totalNotes > 0
      ? ((currentNoteIndex + 1) / totalNotes) * 100
      : 0;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-zinc-900/95 backdrop-blur-lg border-t border-zinc-800">
      {isPlaying && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-zinc-800">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-150 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      <div className="px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <button
              onClick={handlePlayStop}
              disabled={!selectedPattern}
              className={cn(
                "w-11 h-11 rounded-full flex items-center justify-center transition-micro",
                "disabled:bg-zinc-800 disabled:cursor-not-allowed disabled:text-zinc-600",
                isPlaying
                  ? "bg-green-500 hover:bg-green-400 text-white"
                  : "bg-amber-500 hover:bg-amber-400 text-zinc-900"
              )}
            >
              {isPlaying ? (
                <Square className="w-4 h-4 fill-current" />
              ) : (
                <Play className="w-4 h-4 fill-current ml-0.5" />
              )}
            </button>

            <button
              onClick={() => setLoop(!loop)}
              className={cn(
                "p-2 rounded-lg transition-micro",
                loop
                  ? "bg-amber-500/20 text-amber-400"
                  : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
              )}
              title={loop ? "Loop enabled" : "Loop disabled"}
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <button
              onClick={togglePracticeMode}
              className={cn(
                "p-2 rounded-lg transition-micro",
                practiceMode.enabled
                  ? "bg-purple-500/20 text-purple-400"
                  : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
              )}
              title={practiceMode.enabled ? "Practice mode on" : "Practice mode off"}
            >
              <TrendingUp className="w-4 h-4" />
            </button>

            {isPlaying && currentNoteIndex !== null && (
              <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 rounded-lg border border-green-500/20">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-subtle-pulse" />
                <span className="text-mono text-green-400">
                  {currentNoteIndex + 1}/{totalNotes}
                </span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-6">
            {practiceMode.enabled ? (
            <div className="flex items-center gap-3 bg-amber-900/20 px-3 py-1 rounded-lg border border-amber-700/50">
              <span className="text-xs text-amber-400 font-medium">PRACTICE</span>
              <div className="flex items-center gap-1 text-sm text-zinc-300">
                <input
                  type="number"
                  min="40"
                  max="200"
                  value={practiceMode.startTempo}
                  onChange={(e) => setPracticeMode({ startTempo: Number(e.target.value) })}
                  className="w-12 bg-zinc-800 border border-zinc-700 rounded px-1 text-center"
                />
                <span className="text-zinc-500">→</span>
                <input
                  type="number"
                  min="60"
                  max="300"
                  value={practiceMode.endTempo}
                  onChange={(e) => setPracticeMode({ endTempo: Number(e.target.value) })}
                  className="w-12 bg-zinc-800 border border-zinc-700 rounded px-1 text-center"
                />
                <span className="text-zinc-500 text-xs">BPM</span>
              </div>
              <span className="text-zinc-200 font-mono">{tempo}</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <label className="text-sm text-zinc-400">Tempo</label>
              <input
                type="range"
                min="40"
                max="240"
                value={tempo}
                onChange={(e) => setTempo(Number(e.target.value))}
                className="w-24 accent-emerald-500"
              />
              <span className="text-sm text-zinc-200 w-16">{tempo} BPM</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <label className="text-sm text-zinc-400">Root</label>
            <select
              value={rootNote}
              onChange={(e) => setRootNote(Number(e.target.value))}
              className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-200"
            >
              {Array.from({ length: 49 }, (_, i) => i + 36).map((midi) => (
                <option key={midi} value={midi}>
                  {midiToNoteName(midi)}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm text-zinc-400">Octaves</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4].map((n) => (
                <button
                  key={n}
                  onClick={() => setOctaves(n)}
                  className={`w-8 h-8 rounded text-sm font-medium transition-colors ${
                    octaves === n
                      ? "bg-amber-500 text-zinc-900"
                      : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 text-zinc-400">
            <Music className="w-4 h-4" />
            <span className="text-sm truncate max-w-48">
              {selectedPattern ? selectedPattern.name : "Select a pattern"}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
  );
}
