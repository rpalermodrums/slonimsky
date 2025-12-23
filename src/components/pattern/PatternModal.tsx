import { X, Play, Square, Download } from "lucide-react";
import { usePlaybackStore } from "@/stores/playbackStore";
import { usePatternStore } from "@/stores/patternStore";
import { PatternVisualization } from "./PatternVisualization";
import type { SlonimskyPattern } from "@/core/types";

const NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];

interface PatternModalProps {
  pattern: SlonimskyPattern;
  onClose: () => void;
}

export function PatternModal({ pattern, onClose }: PatternModalProps) {
  const { isPlaying, play, stop, rootNote } = usePlaybackStore();
  const { selectedPattern } = usePatternStore();

  const isThisPlaying = isPlaying && selectedPattern?.id === pattern.id;

  const handlePlay = () => {
    if (isThisPlaying) {
      stop();
    } else {
      play(pattern);
    }
  };

  const handleExportMidi = () => {
    const midiData = generateMidiFile(pattern, rootNote);
    const blob = new Blob([midiData], { type: "audio/midi" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${pattern.id}.mid`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const pitchClassNames = pattern.pitchClasses.map((pc) => NOTE_NAMES[pc]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/80" onClick={onClose} />
      
      <div className="relative bg-zinc-900 rounded-xl border border-zinc-800 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-zinc-900 border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">{pattern.name}</h2>
          <button
            onClick={onClose}
            className="p-2 text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <PatternVisualization pattern={pattern} rootNote={rootNote} />

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Category</h3>
              <p className="text-white capitalize">
                {pattern.category.replace(/-/g, " ")}
              </p>
            </div>

            <div className="bg-zinc-800/50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Division</h3>
              <p className="text-white">
                {pattern.division} equal parts ({12 / pattern.division} semitones each)
              </p>
            </div>

            <div className="bg-zinc-800/50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Interpolation</h3>
              <p className="text-white capitalize">
                {pattern.interpolation.type === "none"
                  ? "None"
                  : `${pattern.interpolation.count} ${pattern.interpolation.type}`}
              </p>
            </div>

            <div className="bg-zinc-800/50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Ultrapolation</h3>
              <p className="text-white capitalize">
                {pattern.ultrapolation.type === "none"
                  ? "None"
                  : `${pattern.ultrapolation.semitones} semitones ${pattern.ultrapolation.type}`}
              </p>
            </div>
          </div>

          <div className="bg-zinc-800/50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-zinc-400 mb-2">Pitch Classes</h3>
            <div className="flex flex-wrap gap-2">
              {pitchClassNames.map((name, i) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-zinc-700 rounded-full text-sm text-white font-mono"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-zinc-800/50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-zinc-400 mb-2">Intervals</h3>
            <div className="flex flex-wrap gap-2">
              {pattern.intervals.map((interval, i) => (
                <span
                  key={i}
                  className={`px-3 py-1 rounded-full text-sm font-mono ${
                    interval > 0
                      ? "bg-emerald-900/50 text-emerald-300"
                      : interval < 0
                      ? "bg-rose-900/50 text-rose-300"
                      : "bg-zinc-700 text-zinc-300"
                  }`}
                >
                  {interval > 0 ? `+${interval}` : interval}
                </span>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handlePlay}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors ${
                isThisPlaying
                  ? "bg-rose-600 hover:bg-rose-700 text-white"
                  : "bg-emerald-600 hover:bg-emerald-700 text-white"
              }`}
            >
              {isThisPlaying ? (
                <>
                  <Square className="w-4 h-4" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Play Pattern
                </>
              )}
            </button>

            <button
              onClick={handleExportMidi}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors"
            >
              <Download className="w-4 h-4" />
              MIDI
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function generateMidiFile(pattern: SlonimskyPattern, rootNote: number): Uint8Array {
  const ticksPerBeat = 480;
  const noteDuration = ticksPerBeat;
  
  const events: number[][] = [];
  let currentTick = 0;
  let currentPitch = rootNote;

  for (let i = 0; i < pattern.pitchClasses.length; i++) {
    if (i > 0) {
      currentPitch += pattern.intervals[i - 1];
    }
    
    events.push([currentTick, 0x90, currentPitch, 80]);
    events.push([currentTick + noteDuration - 10, 0x80, currentPitch, 0]);
    currentTick += noteDuration;
  }

  events.push([currentTick, 0xFF, 0x2F, 0]);

  const trackData: number[] = [];
  let lastTick = 0;

  for (const [tick, ...data] of events) {
    const delta = tick - lastTick;
    lastTick = tick;
    trackData.push(...encodeVariableLength(delta), ...data);
  }

  const header = [
    0x4D, 0x54, 0x68, 0x64,
    0x00, 0x00, 0x00, 0x06,
    0x00, 0x00,
    0x00, 0x01,
    (ticksPerBeat >> 8) & 0xFF, ticksPerBeat & 0xFF,
  ];

  const trackHeader = [
    0x4D, 0x54, 0x72, 0x6B,
    (trackData.length >> 24) & 0xFF,
    (trackData.length >> 16) & 0xFF,
    (trackData.length >> 8) & 0xFF,
    trackData.length & 0xFF,
  ];

  return new Uint8Array([...header, ...trackHeader, ...trackData]);
}

function encodeVariableLength(value: number): number[] {
  if (value < 128) return [value];
  
  const bytes: number[] = [];
  bytes.unshift(value & 0x7F);
  value >>= 7;
  
  while (value > 0) {
    bytes.unshift((value & 0x7F) | 0x80);
    value >>= 7;
  }
  
  return bytes;
}
