import { useEffect } from "react";
import { usePlaybackStore } from "@/stores/playbackStore";
import { usePatternStore } from "@/stores/patternStore";

export function useKeyboardShortcuts() {
  const { isPlaying, tempo, setTempo, stop } = usePlaybackStore();
  const { selectedPattern, selectPattern, catalog } = usePatternStore();
  const play = usePlaybackStore((s) => s.play);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.code) {
        case "Space":
          e.preventDefault();
          if (isPlaying) {
            stop();
          } else if (selectedPattern) {
            play(selectedPattern);
          }
          break;

        case "ArrowUp":
          e.preventDefault();
          setTempo(Math.min(200, tempo + 5));
          break;

        case "ArrowDown":
          e.preventDefault();
          setTempo(Math.max(40, tempo - 5));
          break;

        case "ArrowLeft":
        case "ArrowRight": {
          e.preventDefault();
          if (!selectedPattern || catalog.length === 0) break;
          const currentIndex = catalog.findIndex((p) => p.id === selectedPattern.id);
          const direction = e.code === "ArrowRight" ? 1 : -1;
          const newIndex = (currentIndex + direction + catalog.length) % catalog.length;
          selectPattern(catalog[newIndex]);
          break;
        }

        case "Escape":
          if (isPlaying) {
            stop();
          }
          break;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isPlaying, selectedPattern, tempo, setTempo, stop, play, selectPattern, catalog]);
}
