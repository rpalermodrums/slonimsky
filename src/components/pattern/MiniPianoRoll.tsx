import { useMemo } from "react";

interface MiniPianoRollProps {
  intervals: readonly number[];
  isPlaying?: boolean;
  currentNoteIndex?: number;
  height?: number;
}

export function MiniPianoRoll({
  intervals,
  isPlaying = false,
  currentNoteIndex,
  height = 40,
}: MiniPianoRollProps) {
  const { notes, minPitch, maxPitch } = useMemo(() => {
    let pitch = 0;
    const notePositions = [{ pitch: 0, index: 0 }];

    for (let i = 0; i < intervals.length; i++) {
      pitch += intervals[i];
      notePositions.push({ pitch, index: i + 1 });
    }

    const pitches = notePositions.map((n) => n.pitch);
    return {
      notes: notePositions,
      minPitch: Math.min(...pitches),
      maxPitch: Math.max(...pitches),
    };
  }, [intervals]);

  const range = maxPitch - minPitch || 1;
  const padding = 4;
  const noteRadius = 3;

  const getY = (pitch: number) => {
    const normalized = (pitch - minPitch) / range;
    return height - padding - normalized * (height - padding * 2);
  };

  const pathD = useMemo(() => {
    if (notes.length < 2) return "";

    const width = 100;
    const segmentWidth = (width - padding * 2) / (notes.length - 1);

    return notes
      .map((note, i) => {
        const x = padding + i * segmentWidth;
        const y = getY(note.pitch);
        return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
      })
      .join(" ");
  }, [notes, height, minPitch, range]);

  const noteElements = useMemo(() => {
    const width = 100;
    const segmentWidth = (width - padding * 2) / Math.max(notes.length - 1, 1);

    return notes.map((note, i) => {
      const x = padding + i * segmentWidth;
      const y = getY(note.pitch);
      const isActive = currentNoteIndex === i;
      const isRoot = i === 0 || (i > 0 && note.pitch % 12 === 0);

      return {
        x,
        y,
        isActive,
        isRoot,
        index: i,
      };
    });
  }, [notes, currentNoteIndex, height, minPitch, range]);

  return (
    <svg
      viewBox={`0 0 100 ${height}`}
      className="w-full"
      style={{ height }}
      preserveAspectRatio="none"
    >
      <path
        d={pathD}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`text-zinc-600 ${isPlaying ? "text-amber-500/50" : ""}`}
      />

      {noteElements.map((note) => (
        <circle
          key={note.index}
          cx={note.x}
          cy={note.y}
          r={note.isActive ? noteRadius + 1.5 : noteRadius}
          className={`transition-micro ${
            note.isActive
              ? "fill-green-400"
              : note.isRoot
                ? "fill-amber-400"
                : "fill-zinc-400"
          }`}
        />
      ))}

      {isPlaying && currentNoteIndex !== undefined && noteElements[currentNoteIndex] && (
        <circle
          cx={noteElements[currentNoteIndex].x}
          cy={noteElements[currentNoteIndex].y}
          r={noteRadius + 4}
          className="fill-none stroke-green-400/40 animate-pulse-ring"
          strokeWidth={2}
        />
      )}
    </svg>
  );
}
