import { Play, Info } from "lucide-react";
import type { SlonimskyPattern } from "@/core/types";
import { usePatternStore } from "@/stores/patternStore";
import { usePlaybackStore } from "@/stores/playbackStore";

interface PatternCardProps {
  pattern: SlonimskyPattern;
  onOpenModal?: (pattern: SlonimskyPattern) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  "tritone-progression": "bg-purple-500/20 text-purple-300 border-purple-500/30",
  "ditone-progression": "bg-blue-500/20 text-blue-300 border-blue-500/30",
  "sesquitone-progression": "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  "whole-tone-progression": "bg-amber-500/20 text-amber-300 border-amber-500/30",
  "chromatic-progression": "bg-rose-500/20 text-rose-300 border-rose-500/30",
};

function formatCategory(category: string): string {
  return category
    .replace("-progression", "")
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function PatternCard({ pattern, onOpenModal }: PatternCardProps) {
  const { selectedPattern, selectPattern } = usePatternStore();
  const { isPlaying, play, stop, isInitialized, initialize } = usePlaybackStore();

  const isSelected = selectedPattern?.id === pattern.id;
  const isCurrentlyPlaying = isSelected && isPlaying;

  const handleClick = () => {
    selectPattern(pattern);
  };

  const handlePlay = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!isInitialized) {
      await initialize();
    }

    if (isCurrentlyPlaying) {
      stop();
    } else {
      selectPattern(pattern);
      play(pattern);
    }
  };

  const categoryClass = CATEGORY_COLORS[pattern.category] || "bg-zinc-500/20 text-zinc-300";

  return (
    <div
      onClick={handleClick}
      className={`group relative p-4 rounded-xl border transition-all cursor-pointer ${
        isSelected
          ? "bg-zinc-800 border-emerald-500/50 ring-1 ring-emerald-500/20"
          : "bg-zinc-900 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/50"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-zinc-100 truncate">{pattern.name}</h3>
          <p className="text-sm text-zinc-500 mt-1">ID: {pattern.id}</p>
        </div>

        <div className="flex gap-1">
          {onOpenModal && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onOpenModal(pattern);
              }}
              className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all bg-zinc-700 text-zinc-300 opacity-0 group-hover:opacity-100 hover:bg-zinc-600 hover:text-white"
              title="View details"
            >
              <Info className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={handlePlay}
            className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
              isCurrentlyPlaying
                ? "bg-emerald-500 text-white"
                : "bg-zinc-700 text-zinc-300 opacity-0 group-hover:opacity-100 hover:bg-emerald-600 hover:text-white"
            }`}
          >
            <Play className={`w-4 h-4 ${isCurrentlyPlaying ? "" : "ml-0.5"}`} />
          </button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <span className={`text-xs px-2 py-1 rounded-full border ${categoryClass}`}>
          {formatCategory(pattern.category)}
        </span>

        {pattern.interpolation.type !== "none" && (
          <span className="text-xs px-2 py-1 rounded-full bg-zinc-800 text-zinc-400">
            {pattern.interpolation.count} {pattern.interpolation.type}
          </span>
        )}

        {pattern.ultrapolation.type !== "none" && (
          <span className="text-xs px-2 py-1 rounded-full bg-zinc-800 text-zinc-400">
            Ultra: {pattern.ultrapolation.type}
          </span>
        )}
      </div>

      <div className="mt-3 flex gap-1">
        {pattern.intervals.slice(0, 12).map((interval, i) => (
          <div
            key={i}
            className="h-6 bg-zinc-700 rounded-sm flex items-center justify-center text-xs text-zinc-400"
            style={{ width: `${Math.max(16, Math.abs(interval) * 8)}px` }}
            title={`${interval > 0 ? "+" : ""}${interval.toFixed(1)} semitones`}
          >
            {Number.isInteger(interval) ? interval : interval.toFixed(1)}
          </div>
        ))}
        {pattern.intervals.length > 12 && (
          <span className="text-xs text-zinc-500 self-center ml-1">
            +{pattern.intervals.length - 12} more
          </span>
        )}
      </div>
    </div>
  );
}
