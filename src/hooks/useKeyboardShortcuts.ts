import { useEffect, useCallback } from "react";
import { usePlaybackStore } from "@/stores/playbackStore";
import { usePatternStore } from "@/stores/patternStore";
import type { SlonimskyPattern } from "@/core/types";

interface KeyboardShortcutsOptions {
  patterns: SlonimskyPattern[];
  gridColumns?: number;
  onFocusSearch?: () => void;
}

export function useKeyboardShortcuts({
  patterns,
  gridColumns = 3,
  onFocusSearch,
}: KeyboardShortcutsOptions) {
  const { isPlaying, tempo, setTempo, stop, isInitialized, initialize, toggleDirection } = usePlaybackStore();
  const { selectedPattern, selectPattern, selectRandomPattern, toggleMastered } = usePatternStore();
  const play = usePlaybackStore((s) => s.play);

  const handleKeyDown = useCallback(
    async (e: KeyboardEvent) => {
      const isInInput =
        e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;

      if (e.key === "/" && !isInInput) {
        e.preventDefault();
        onFocusSearch?.();
        return;
      }

      if (e.key === "Escape") {
        if (isInInput) {
          (e.target as HTMLElement).blur();
        } else if (isPlaying) {
          stop();
        }
        return;
      }

      if (isInInput) return;

      switch (e.code) {
        case "Space":
          e.preventDefault();
          if (isPlaying) {
            stop();
          } else if (selectedPattern) {
            if (!isInitialized) await initialize();
            play(selectedPattern);
          }
          break;

        case "ArrowUp":
        case "ArrowDown":
        case "ArrowLeft":
        case "ArrowRight": {
          e.preventDefault();
          if (patterns.length === 0) break;

          const currentIndex = selectedPattern
            ? patterns.findIndex((p) => p.id === selectedPattern.id)
            : -1;

          let newIndex = currentIndex;

          if (e.code === "ArrowRight") {
            newIndex = currentIndex < patterns.length - 1 ? currentIndex + 1 : 0;
          } else if (e.code === "ArrowLeft") {
            newIndex = currentIndex > 0 ? currentIndex - 1 : patterns.length - 1;
          } else if (e.code === "ArrowDown") {
            newIndex = currentIndex + gridColumns;
            if (newIndex >= patterns.length) newIndex = currentIndex % gridColumns;
          } else if (e.code === "ArrowUp") {
            newIndex = currentIndex - gridColumns;
            if (newIndex < 0) {
              const lastRowStart =
                Math.floor((patterns.length - 1) / gridColumns) * gridColumns;
              newIndex = Math.min(lastRowStart + (currentIndex % gridColumns), patterns.length - 1);
            }
          }

          if (newIndex >= 0 && newIndex < patterns.length) {
            selectPattern(patterns[newIndex]);
          }
          break;
        }

        case "BracketRight":
          e.preventDefault();
          setTempo(Math.min(240, tempo + 5));
          break;

        case "BracketLeft":
          e.preventDefault();
          setTempo(Math.max(40, tempo - 5));
          break;

        case "Enter":
          e.preventDefault();
          if (selectedPattern) {
            if (!isInitialized) await initialize();
            play(selectedPattern);
          }
          break;

        case "KeyR":
          if (!e.metaKey && !e.ctrlKey) {
            e.preventDefault();
            selectRandomPattern();
          }
          break;

        case "KeyM":
          e.preventDefault();
          if (selectedPattern) {
            toggleMastered(selectedPattern.id);
          }
          break;

        case "KeyD":
          e.preventDefault();
          toggleDirection();
          break;
      }
    },
    [
      isPlaying,
      selectedPattern,
      patterns,
      gridColumns,
      tempo,
      setTempo,
      stop,
      play,
      selectPattern,
      selectRandomPattern,
      toggleMastered,
      toggleDirection,
      onFocusSearch,
      isInitialized,
      initialize,
    ]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}
