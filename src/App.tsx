import { useState, useMemo, useRef, useCallback } from "react";
import { Search, Music, LayoutGrid, GitBranch, BarChart3 } from "lucide-react";
import { PatternCard } from "@/components/pattern/PatternCard";
import { PatternModal } from "@/components/pattern/PatternModal";
import { PatternVisualization } from "@/components/pattern/PatternVisualization";
import { TransportBar } from "@/components/transport/TransportBar";
import { PianoKeyboard } from "@/components/piano/PianoKeyboard";
import { GraphView } from "@/components/graph/GraphView";
import { usePatternStore } from "@/stores/patternStore";
import { usePlaybackStore } from "@/stores/playbackStore";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { pitchClassesToMidi } from "@/core";
import type { PatternCategory, SlonimskyPattern } from "@/core/types";

type ViewMode = "patterns" | "graph";

const CATEGORIES: { value: PatternCategory | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "tritone-progression", label: "Tritone" },
  { value: "ditone-progression", label: "Ditone" },
  { value: "sesquitone-progression", label: "Sesquitone" },
  { value: "whole-tone-progression", label: "Whole Tone" },
  { value: "chromatic-progression", label: "Chromatic" },
];

function App() {
  const { catalog, selectedPattern } = usePatternStore();
  const { currentNote, rootNote, octaves } = usePlaybackStore();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<PatternCategory | "all">("all");
  const [viewMode, setViewMode] = useState<ViewMode>("patterns");
  const [showVisualization, setShowVisualization] = useState(false);
  const [modalPattern, setModalPattern] = useState<SlonimskyPattern | null>(null);
  const [isPianoExpanded, setIsPianoExpanded] = useState(false);

  const searchInputRef = useRef<HTMLInputElement>(null);

  const patternNotes = useMemo(() => {
    if (!selectedPattern) return [];
    const notes: number[] = [];
    for (let o = 0; o < octaves; o++) {
      const octaveNotes = pitchClassesToMidi(
        selectedPattern.pitchClasses,
        rootNote + o * 12,
        selectedPattern.intervals
      );
      notes.push(...octaveNotes);
    }
    return notes;
  }, [selectedPattern, rootNote, octaves]);

  const filteredPatterns = useMemo(() => {
    return catalog.filter((pattern) => {
      const matchesSearch =
        search === "" ||
        pattern.name.toLowerCase().includes(search.toLowerCase()) ||
        pattern.id.toLowerCase().includes(search.toLowerCase());

      const matchesCategory =
        categoryFilter === "all" || pattern.category === categoryFilter;

      return matchesSearch && matchesCategory;
    });
  }, [catalog, search, categoryFilter]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
  }, []);

  useKeyboardShortcuts({
    patterns: filteredPatterns,
    gridColumns: 3,
    onFocusSearch: handleFocusSearch,
  });

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      <header className="sticky top-0 z-20 bg-zinc-950/80 backdrop-blur-lg border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center">
                <Music className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Slonimsky</h1>
                <p className="text-xs text-zinc-500">Pattern Practice</p>
              </div>
            </div>

            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search patterns... (press /)"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm placeholder:text-zinc-600 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/20"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-zinc-900 p-1 rounded-lg">
                <button
                  onClick={() => setViewMode("patterns")}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === "patterns"
                      ? "bg-zinc-700 text-white"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                  title="Pattern Grid"
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode("graph")}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === "graph"
                      ? "bg-zinc-700 text-white"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                  title="Melodic Graph"
                >
                  <GitBranch className="w-4 h-4" />
                </button>
              </div>

              <div className="w-px h-6 bg-zinc-800" />

              <button
                onClick={() => setShowVisualization(!showVisualization)}
                className={`p-2 rounded-lg transition-micro ${
                  showVisualization
                    ? "bg-amber-500/20 text-amber-400"
                    : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                }`}
                title="Toggle Pattern Visualization"
              >
                <BarChart3 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <main className={`flex-1 overflow-y-auto ${showVisualization && selectedPattern ? "mr-80" : ""}`}>
          <div className="max-w-6xl mx-auto px-6 py-6 pb-32">
            {viewMode === "patterns" ? (
              <>
                <div className="flex items-center gap-2 mb-6 flex-wrap">
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat.value}
                      onClick={() => setCategoryFilter(cat.value)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        categoryFilter === cat.value
                          ? "bg-emerald-600 text-white"
                          : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                  <span className="ml-auto text-sm text-zinc-500">
                    {filteredPatterns.length} patterns
                  </span>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {filteredPatterns.map((pattern) => (
                    <PatternCard key={pattern.id} pattern={pattern} onOpenModal={setModalPattern} />
                  ))}
                </div>

                {filteredPatterns.length === 0 && (
                  <div className="text-center py-12 text-zinc-500">
                    No patterns match your search.
                  </div>
                )}
              </>
            ) : (
              <GraphView />
            )}
          </div>
        </main>

        {showVisualization && selectedPattern && (
          <aside className="fixed right-0 top-[73px] bottom-[72px] w-80 bg-zinc-900/50 backdrop-blur-lg border-l border-zinc-800 overflow-y-auto z-10">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-zinc-300">Pattern Visualization</h3>
                <button
                  onClick={() => setShowVisualization(false)}
                  className="text-zinc-500 hover:text-zinc-300"
                >
                  ×
                </button>
              </div>
              <div className="space-y-4">
                <div className="bg-zinc-900 rounded-lg p-3">
                  <h4 className="text-xs text-zinc-500 mb-1">Selected</h4>
                  <p className="font-medium">{selectedPattern.name}</p>
                  <p className="text-xs text-zinc-500 mt-1">{selectedPattern.id}</p>
                </div>
                <PatternVisualization
                  pattern={selectedPattern}
                  rootNote={rootNote}
                  currentNoteIndex={currentNote !== null ? patternNotes.indexOf(currentNote) : undefined}
                />
                <div className="bg-zinc-900 rounded-lg p-3 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Division</span>
                    <span>{selectedPattern.division}-tone</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Interpolation</span>
                    <span>{selectedPattern.interpolation.type} ({selectedPattern.interpolation.count})</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Ultrapolation</span>
                    <span>{selectedPattern.ultrapolation.type} ({selectedPattern.ultrapolation.semitones})</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Notes</span>
                    <span>{selectedPattern.pitchClasses.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        )}
      </div>

      <div
        className="fixed bottom-[72px] left-0 right-0 bg-zinc-900/95 backdrop-blur-lg border-t border-zinc-800 z-10"
        onMouseEnter={() => setIsPianoExpanded(true)}
        onMouseLeave={() => setIsPianoExpanded(false)}
      >
        <div className="max-w-4xl mx-auto px-4 py-2">
          <PianoKeyboard
            startNote={Math.max(36, rootNote - 12)}
            endNote={Math.min(96, rootNote + 24 + (octaves - 1) * 12)}
            activeNotes={currentNote !== null ? [currentNote] : []}
            highlightedNotes={patternNotes}
            compact={!isPianoExpanded}
          />
        </div>
      </div>

      <TransportBar />

      {modalPattern && (
        <PatternModal
          pattern={modalPattern}
          onClose={() => setModalPattern(null)}
        />
      )}
    </div>
  );
}

export default App;
