import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface PianoKeyboardProps {
  startNote?: number;
  endNote?: number;
  activeNotes?: number[];
  highlightedNotes?: number[];
  onNoteClick?: (note: number) => void;
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

  return (
    <div className="relative w-full h-32 select-none">
      {whiteKeys.map((key, index) => (
        <button
          key={key.midi}
          onClick={() => onNoteClick?.(key.midi)}
          className={cn(
            "absolute top-0 h-full border border-zinc-300 rounded-b-md transition-colors",
            "hover:bg-zinc-100",
            activeSet.has(key.midi) && "bg-blue-500 border-blue-600",
            highlightSet.has(key.midi) && !activeSet.has(key.midi) && "bg-blue-200",
            !activeSet.has(key.midi) && !highlightSet.has(key.midi) && "bg-white"
          )}
          style={{
            left: `${index * whiteKeyWidth}%`,
            width: `${whiteKeyWidth}%`,
          }}
          aria-label={key.name}
        >
          <span className="absolute bottom-1 left-1/2 -translate-x-1/2 text-xs text-zinc-400">
            {key.name.replace("#", "")}
          </span>
        </button>
      ))}

      {blackKeys.map((key) => {
        const octaveStart = Math.floor(key.midi / 12) * 12;
        const noteInOctave = key.midi % 12;
        const octaveStartWhiteIndex = whiteKeys.findIndex(
          (w) => w.midi >= octaveStart && !isBlackKey(w.midi)
        );
        const offset = getBlackKeyOffset(noteInOctave);
        const leftPos = (octaveStartWhiteIndex + offset) * whiteKeyWidth;

        return (
          <button
            key={key.midi}
            onClick={() => onNoteClick?.(key.midi)}
            className={cn(
              "absolute top-0 h-[60%] rounded-b-md z-10 transition-colors",
              activeSet.has(key.midi) && "bg-blue-600",
              highlightSet.has(key.midi) && !activeSet.has(key.midi) && "bg-blue-400",
              !activeSet.has(key.midi) && !highlightSet.has(key.midi) && "bg-zinc-800"
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
