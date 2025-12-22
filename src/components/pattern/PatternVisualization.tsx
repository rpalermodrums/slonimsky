import type { SlonimskyPattern } from "@/core/types";
import { pitchClassesToMidi } from "@/core";

interface PatternVisualizationProps {
  pattern: SlonimskyPattern;
  rootNote?: number;
  currentNoteIndex?: number;
  height?: number;
}

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

export function PatternVisualization({
  pattern,
  rootNote = 60,
  currentNoteIndex,
  height = 120,
}: PatternVisualizationProps) {
  const midiNotes = pitchClassesToMidi(pattern.pitchClasses, rootNote);
  const minNote = Math.min(...midiNotes);
  const maxNote = Math.max(...midiNotes);
  const range = maxNote - minNote + 1;

  const noteWidth = 100 / midiNotes.length;
  const noteHeight = height / Math.max(range, 12);

  return (
    <div className="w-full bg-zinc-900 rounded-lg p-4">
      <svg
        viewBox={`0 0 100 ${height}`}
        className="w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {Array.from({ length: range }).map((_, i) => {
          const note = maxNote - i;
          const pitchClass = note % 12;
          const isBlackKey = [1, 3, 6, 8, 10].includes(pitchClass);

          return (
            <g key={i}>
              <rect
                x={0}
                y={i * noteHeight}
                width={100}
                height={noteHeight}
                fill={isBlackKey ? "rgb(39 39 42)" : "rgb(63 63 70)"}
                stroke="rgb(82 82 91)"
                strokeWidth={0.2}
              />
              <text
                x={2}
                y={i * noteHeight + noteHeight / 2 + 1}
                fontSize={Math.min(noteHeight * 0.6, 4)}
                fill="rgb(161 161 170)"
                dominantBaseline="middle"
              >
                {NOTE_NAMES[pitchClass]}
              </text>
            </g>
          );
        })}

        {midiNotes.map((note, index) => {
          const x = index * noteWidth + noteWidth * 0.1;
          const y = (maxNote - note) * noteHeight + noteHeight * 0.1;
          const w = noteWidth * 0.8;
          const h = noteHeight * 0.8;
          const isActive = currentNoteIndex === index;
          const isFirst = index === 0;
          const isLast = index === midiNotes.length - 1;

          return (
            <rect
              key={index}
              x={x}
              y={y}
              width={w}
              height={h}
              rx={1}
              fill={
                isActive
                  ? "rgb(34 197 94)"
                  : isFirst || isLast
                    ? "rgb(168 85 247)"
                    : "rgb(59 130 246)"
              }
              opacity={isActive ? 1 : 0.8}
              className={isActive ? "animate-pulse" : ""}
            />
          );
        })}

        {midiNotes.slice(1).map((note, index) => {
          const prevNote = midiNotes[index];
          const x1 = index * noteWidth + noteWidth * 0.9;
          const y1 = (maxNote - prevNote) * noteHeight + noteHeight * 0.5;
          const x2 = (index + 1) * noteWidth + noteWidth * 0.1;
          const y2 = (maxNote - note) * noteHeight + noteHeight * 0.5;

          return (
            <line
              key={`line-${index}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="rgb(161 161 170)"
              strokeWidth={0.3}
              strokeDasharray="1,1"
            />
          );
        })}
      </svg>

      <div className="mt-2 flex justify-between text-xs text-zinc-500">
        <span>Start</span>
        <span>{midiNotes.length} notes</span>
        <span>End</span>
      </div>
    </div>
  );
}
