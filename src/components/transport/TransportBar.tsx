import { Play, Square, RotateCcw, Volume2, TrendingUp } from "lucide-react";
import { usePlaybackStore } from "@/stores/playbackStore";
import { usePatternStore } from "@/stores/patternStore";

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

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-700 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <button
            onClick={handlePlayStop}
            disabled={!selectedPattern}
            className="w-12 h-12 rounded-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            {isPlaying ? (
              <Square className="w-5 h-5 text-white fill-white" />
            ) : (
              <Play className="w-5 h-5 text-white fill-white ml-1" />
            )}
          </button>

          <button
            onClick={() => setLoop(!loop)}
            className={`p-2 rounded-lg transition-colors ${
              loop
                ? "bg-emerald-600/20 text-emerald-400"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
            title={loop ? "Loop enabled" : "Loop disabled"}
          >
            <RotateCcw className="w-5 h-5" />
          </button>

          <button
            onClick={togglePracticeMode}
            className={`p-2 rounded-lg transition-colors ${
              practiceMode.enabled
                ? "bg-amber-600/20 text-amber-400"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
            title={practiceMode.enabled ? "Practice mode on" : "Practice mode off"}
          >
            <TrendingUp className="w-5 h-5" />
          </button>
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
                      ? "bg-emerald-600 text-white"
                      : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-zinc-400">
          <Volume2 className="w-5 h-5" />
          <span className="text-sm">
            {selectedPattern ? selectedPattern.name : "Select a pattern"}
          </span>
        </div>
      </div>
    </div>
  );
}
