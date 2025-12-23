import { Play, Square, RotateCcw, TrendingUp, Music, Timer, ArrowUp, ArrowDown, Shuffle, ChevronLeft, ChevronRight } from "lucide-react";
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
    isCountingIn,
    countInEnabled,
    currentCountInBeat,
    tempo,
    rootNote,
    octaves,
    noteDuration,
    direction,
    loop,
    practiceMode,
    currentNoteIndex,
    initialize,
    play,
    stop,
    setTempo,
    setRootNote,
    setOctaves,
    setNoteDuration,
    toggleDirection,
    setLoop,
    setCountInEnabled,
    togglePracticeMode,
  } = usePlaybackStore();

  const { selectedPattern, selectRandomPattern, selectNextPattern, selectPreviousPattern } = usePatternStore();

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

  const totalNotes = selectedPattern ? selectedPattern.pitchClasses.length * octaves : 0;
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
              onClick={selectPreviousPattern}
              className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition-micro"
              title="Previous pattern"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

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
              onClick={selectNextPattern}
              className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition-micro"
              title="Next pattern"
            >
              <ChevronRight className="w-4 h-4" />
            </button>

            <button
              onClick={selectRandomPattern}
              className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition-micro"
              title="Random pattern"
            >
              <Shuffle className="w-4 h-4" />
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
              onClick={toggleDirection}
              className={cn(
                "p-2 rounded-lg transition-micro",
                direction === "descending"
                  ? "bg-rose-500/20 text-rose-400"
                  : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
              )}
              title={direction === "ascending" ? "Ascending (click to reverse)" : "Descending (click to reverse)"}
            >
              {direction === "ascending" ? (
                <ArrowUp className="w-4 h-4" />
              ) : (
                <ArrowDown className="w-4 h-4" />
              )}
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

            <button
              onClick={() => setCountInEnabled(!countInEnabled)}
              className={cn(
                "p-2 rounded-lg transition-micro",
                countInEnabled
                  ? "bg-cyan-500/20 text-cyan-400"
                  : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
              )}
              title={countInEnabled ? "Count-in enabled" : "Count-in disabled"}
            >
              <Timer className="w-4 h-4" />
            </button>

            {isCountingIn && currentCountInBeat !== null && (
              <div className="flex items-center gap-2 px-4 py-1 bg-cyan-500/10 rounded-lg border border-cyan-500/20">
                <span className="text-2xl font-bold text-cyan-400 animate-pulse">
                  {currentCountInBeat}
                </span>
              </div>
            )}

            {isPlaying && !isCountingIn && currentNoteIndex !== null && (
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
            <div className="flex items-center gap-3 bg-purple-900/20 px-3 py-2 rounded-lg border border-purple-700/50">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-purple-400 font-medium">PRACTICE</span>
                  <span className="text-lg font-bold text-purple-300">{tempo}</span>
                  <span className="text-xs text-zinc-500">/ {practiceMode.endTempo} BPM</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-300"
                      style={{ 
                        width: `${Math.min(100, ((tempo - practiceMode.startTempo) / (practiceMode.endTempo - practiceMode.startTempo)) * 100)}%` 
                      }}
                    />
                  </div>
                  <span className="text-xs text-zinc-500">
                    Loop {practiceMode.currentLoopCount + 1}/{practiceMode.loopsPerTempo}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1 text-xs text-zinc-400">
                <span>{practiceMode.startTempo}</span>
                <span>→</span>
                <span>{practiceMode.endTempo}</span>
                <span className="text-zinc-600">+{practiceMode.incrementBpm}</span>
              </div>
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

          <div className="flex items-center gap-2">
            <label className="text-sm text-zinc-400">Duration</label>
            <select
              value={noteDuration}
              onChange={(e) => setNoteDuration(Number(e.target.value))}
              className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-200"
            >
              <option value={0.25}>♬ 1/4</option>
              <option value={0.5}>♩ 1/2</option>
              <option value={0.75}>♩. 3/4</option>
              <option value={1}>𝅗𝅥 1</option>
            </select>
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
