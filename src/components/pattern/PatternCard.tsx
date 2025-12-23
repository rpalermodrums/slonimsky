import { useRef, useCallback, useState } from "react";
import { Play, Pause, ChevronDown, ChevronUp, Download } from "lucide-react";
import type { SlonimskyPattern } from "@/core/types";
import { usePatternStore } from "@/stores/patternStore";
import { usePlaybackStore } from "@/stores/playbackStore";
import { MiniPianoRoll } from "./MiniPianoRoll";
import { PatternVisualization } from "./PatternVisualization";

interface PatternCardProps {
  pattern: SlonimskyPattern;
  onOpenModal?: (pattern: SlonimskyPattern) => void;
  onExport?: (pattern: SlonimskyPattern) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  "tritone-progression": "bg-purple-500/10 text-purple-300 border-purple-500/20",
  "ditone-progression": "bg-blue-500/10 text-blue-300 border-blue-500/20",
  "sesquitone-progression": "bg-cyan-500/10 text-cyan-300 border-cyan-500/20",
  "whole-tone-progression": "bg-amber-500/10 text-amber-300 border-amber-500/20",
  "chromatic-progression": "bg-rose-500/10 text-rose-300 border-rose-500/20",
};

const CATEGORY_ACCENT: Record<string, string> = {
  "tritone-progression": "border-l-purple-500",
  "ditone-progression": "border-l-blue-500",
  "sesquitone-progression": "border-l-cyan-500",
  "whole-tone-progression": "border-l-amber-500",
  "chromatic-progression": "border-l-rose-500",
};

function formatCategory(category: string): string {
  return category
    .replace("-progression", "")
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function PatternCard({ pattern, onOpenModal, onExport }: PatternCardProps) {
  const { selectedPattern, selectPattern } = usePatternStore();
  const {
    isPlaying,
    isPreviewing,
    play,
    stop,
    preview,
    stopPreview,
    isInitialized,
    initialize,
    currentNoteIndex,
    rootNote,
  } = usePlaybackStore();

  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const isSelected = selectedPattern?.id === pattern.id;
  const isCurrentlyPlaying = isSelected && isPlaying;

  const handleMouseEnter = useCallback(async () => {
    if (isPlaying) return;

    hoverTimeoutRef.current = setTimeout(async () => {
      if (!isInitialized) {
        await initialize();
      }
      preview(pattern);
    }, 400);
  }, [isPlaying, isInitialized, initialize, preview, pattern]);

  const handleMouseLeave = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
    if (isPreviewing) {
      stopPreview();
    }
  }, [isPreviewing, stopPreview]);

  const handleClick = () => {
    if (isSelected) {
      setIsExpanded(!isExpanded);
    } else {
      selectPattern(pattern);
    }
  };

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    selectPattern(pattern);
    setIsExpanded(!isExpanded);
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

  const categoryClass = CATEGORY_COLORS[pattern.category] || "bg-zinc-500/10 text-zinc-300";
  const accentClass = CATEGORY_ACCENT[pattern.category] || "border-l-zinc-500";

  return (
    <div
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`group relative rounded-xl border border-l-[3px] transition-standard cursor-pointer overflow-hidden ${accentClass} ${
        isSelected
          ? "bg-zinc-800/80 border-amber-500/30 ring-1 ring-amber-500/20"
          : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/50"
      } ${isPreviewing ? "ring-1 ring-amber-500/30" : ""}`}
    >
      <div className="p-3 bg-zinc-900/30">
        <MiniPianoRoll
          intervals={pattern.intervals}
          isPlaying={isCurrentlyPlaying}
          currentNoteIndex={isCurrentlyPlaying ? currentNoteIndex ?? undefined : undefined}
          height={48}
        />
      </div>

      <div className="p-4 pt-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-title text-zinc-100 truncate">{pattern.name}</h3>
            <p className="text-mono text-zinc-500 mt-1">{pattern.id}</p>
          </div>

          <div className="flex gap-1.5">
            <button
              onClick={handleToggleExpand}
              className={`shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-micro ${
                isExpanded
                  ? "bg-amber-500/20 text-amber-400"
                  : "bg-zinc-800 text-zinc-400 opacity-0 group-hover:opacity-100 hover:bg-zinc-700 hover:text-zinc-200"
              }`}
              title={isExpanded ? "Collapse" : "Expand details"}
            >
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={handlePlay}
              className={`shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-micro ${
                isCurrentlyPlaying
                  ? "bg-green-500 text-white"
                  : "bg-amber-500/90 text-zinc-900 opacity-0 group-hover:opacity-100 hover:bg-amber-400"
              }`}
            >
              {isCurrentlyPlaying ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4 ml-0.5" />
              )}
            </button>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className={`text-xs px-2 py-0.5 rounded border ${categoryClass}`}>
            {formatCategory(pattern.category)}
          </span>

          {pattern.interpolation.type !== "none" && (
            <span className="text-xs px-2 py-0.5 rounded bg-zinc-800/50 text-zinc-400 border border-zinc-700/50">
              {pattern.interpolation.count} {pattern.interpolation.type}
            </span>
          )}

          {pattern.ultrapolation.type !== "none" && (
            <span className="text-xs px-2 py-0.5 rounded bg-zinc-800/50 text-zinc-400 border border-zinc-700/50">
              Ultra {pattern.ultrapolation.type}
            </span>
          )}
        </div>
      </div>

      <div
        className={`overflow-hidden transition-all duration-300 ease-out ${
          isExpanded ? "max-h-[300px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="p-4 pt-0 border-t border-zinc-800/50">
          <PatternVisualization
            pattern={pattern}
            rootNote={rootNote}
            currentNoteIndex={isCurrentlyPlaying ? (currentNoteIndex ?? undefined) : undefined}
            height={160}
          />

          <div className="mt-3 flex items-center justify-between">
            <div className="text-xs text-zinc-500">
              <span className="text-zinc-400">{pattern.intervals.length}</span> intervals •{" "}
              <span className="text-zinc-400">{pattern.pitchClasses.length}</span> pitch classes
            </div>

            <div className="flex gap-2">
              {onExport && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onExport(pattern);
                  }}
                  className="px-3 py-1.5 text-xs rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 transition-micro flex items-center gap-1.5"
                >
                  <Download className="w-3 h-3" />
                  Export MIDI
                </button>
              )}
              {onOpenModal && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onOpenModal(pattern);
                  }}
                  className="px-3 py-1.5 text-xs rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 transition-micro"
                >
                  Full Details
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {isCurrentlyPlaying && (
        <div className="absolute inset-0 pointer-events-none border-2 border-green-500/30 rounded-xl animate-subtle-pulse" />
      )}
    </div>
  );
}
