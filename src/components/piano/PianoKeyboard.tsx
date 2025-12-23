import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface PianoKeyboardProps {
  startNote?: number;
  endNote?: number;
  activeNotes?: number[];
  highlightedNotes?: number[];
  onNoteClick?: (note: number) => void;
  compact?: boolean;
}

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

function isBlackKey(midiNote: number): boolean {
  const noteInOctave = midiNote % 12;
  return [1, 3, 6, 8, 10].includes(noteInOctave);
}

function getNoteName(midiNote: number): string {
  const octave = Math.floor(midiNote / 12) - 1;
  const noteName = NOTE_NAMES[midiNote % 12];
  return `${noteName}${octave}`;
}

function getBlackKeyOffset(noteInOctave: number): number {
  const offsets: Record<number, number> = {
    1: 0.6,
    3: 1.8,
    6: 3.6,
    8: 4.7,
    10: 5.8,
  };
  return offsets[noteInOctave] ?? 0;
}

export function PianoKeyboard({
  startNote = 48,
  endNote = 84,
  activeNotes = [],
  highlightedNotes = [],
  onNoteClick,
  compact = false,
}: PianoKeyboardProps) {
  const keys = useMemo(() => {
    const result: Array<{
      midi: number;
      isBlack: boolean;
      name: string;
      whiteKeyIndex: number;
    }> = [];

    let whiteKeyIndex = 0;
    for (let midi = startNote; midi <= endNote; midi++) {
      const isBlack = isBlackKey(midi);
      result.push({
        midi,
        isBlack,
        name: getNoteName(midi),
        whiteKeyIndex: isBlack ? whiteKeyIndex - 1 : whiteKeyIndex,
      });
      if (!isBlack) whiteKeyIndex++;
    }

    return result;
  }, [startNote, endNote]);

  const whiteKeys = keys.filter((k) => !k.isBlack);
  const blackKeys = keys.filter((k) => k.isBlack);
  const whiteKeyWidth = 100 / whiteKeys.length;

  const activeSet = new Set(activeNotes);
  const highlightSet = new Set(highlightedNotes);

  const height = compact ? "h-12" : "h-24";
  const blackKeyHeight = compact ? "h-[55%]" : "h-[60%]";

  return (
    <div className={cn("relative w-full select-none transition-all duration-300", height)}>
      {whiteKeys.map((key, index) => {
        const isActive = activeSet.has(key.midi);
        const isHighlighted = highlightSet.has(key.midi);

        return (
          <button
            key={key.midi}
            onClick={() => onNoteClick?.(key.midi)}
            className={cn(
              "absolute top-0 h-full rounded-b transition-micro",
              "border border-zinc-300/50",
              "bg-gradient-to-b from-zinc-100 to-zinc-200",
              "hover:from-zinc-50 hover:to-zinc-100",
              isActive && "from-green-400 to-green-500 border-green-500 glow-note animate-key-press",
              isHighlighted && !isActive && "from-amber-100 to-amber-200 border-amber-300/50"
            )}
            style={{
              left: `${index * whiteKeyWidth}%`,
              width: `${whiteKeyWidth}%`,
            }}
            aria-label={key.name}
          >
            {!compact && (
              <span
                className={cn(
                  "absolute bottom-1 left-1/2 -translate-x-1/2 text-[10px] font-medium",
                  isActive ? "text-white" : "text-zinc-400"
                )}
              >
                {key.name.replace("#", "")}
              </span>
            )}
          </button>
        );
      })}

      {blackKeys.map((key) => {
        const octaveStart = Math.floor(key.midi / 12) * 12;
        const noteInOctave = key.midi % 12;
        const octaveStartWhiteIndex = whiteKeys.findIndex(
          (w) => w.midi >= octaveStart && !isBlackKey(w.midi)
        );
        const offset = getBlackKeyOffset(noteInOctave);
        const leftPos = (octaveStartWhiteIndex + offset) * whiteKeyWidth;

        const isActive = activeSet.has(key.midi);
        const isHighlighted = highlightSet.has(key.midi);

        return (
          <button
            key={key.midi}
            onClick={() => onNoteClick?.(key.midi)}
            className={cn(
              "absolute top-0 rounded-b z-10 transition-micro",
              "bg-gradient-to-b from-zinc-700 to-zinc-900",
              "hover:from-zinc-600 hover:to-zinc-800",
              "shadow-md",
              blackKeyHeight,
              isActive && "from-green-500 to-green-600 glow-note animate-key-press",
              isHighlighted && !isActive && "from-amber-500/60 to-amber-600/60"
            )}
            style={{
              left: `${leftPos}%`,
              width: `${whiteKeyWidth * 0.6}%`,
            }}
            aria-label={key.name}
          />
        );
      })}
    </div>
  );
}
