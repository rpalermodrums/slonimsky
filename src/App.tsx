import { useState, useMemo } from "react";
import { Search, Music } from "lucide-react";
import { PatternCard } from "@/components/pattern/PatternCard";
import { PatternVisualization } from "@/components/pattern/PatternVisualization";
import { TransportBar } from "@/components/transport/TransportBar";
import { PianoKeyboard } from "@/components/piano/PianoKeyboard";
import { usePatternStore } from "@/stores/patternStore";
import { usePlaybackStore } from "@/stores/playbackStore";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { pitchClassesToMidi } from "@/core";
import type { PatternCategory } from "@/core/types";

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

  useKeyboardShortcuts();

  const patternNotes = useMemo(() => {
    if (!selectedPattern) return [];
    const notes: number[] = [];
    for (let o = 0; o < octaves; o++) {
      const octaveNotes = pitchClassesToMidi(selectedPattern.pitchClasses, rootNote + o * 12);
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

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-10 bg-zinc-950/80 backdrop-blur-lg border-b border-zinc-800">
        <div className="max-w-6xl mx-auto px-6 py-4">
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
                  type="text"
                  placeholder="Search patterns..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700"
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 py-4 space-y-4">
        <PianoKeyboard
          startNote={Math.max(36, rootNote - 12)}
          endNote={Math.min(96, rootNote + 24 + (octaves - 1) * 12)}
          activeNotes={currentNote !== null ? [currentNote] : []}
          highlightedNotes={patternNotes}
        />
        {selectedPattern && (
          <PatternVisualization
            pattern={selectedPattern}
            rootNote={rootNote}
            currentNoteIndex={currentNote !== null ? patternNotes.indexOf(currentNote) : undefined}
          />
        )}
      </section>

      <main className="max-w-6xl mx-auto px-6 py-6 pb-32">
        <div className="flex items-center gap-2 mb-6">
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
            <PatternCard key={pattern.id} pattern={pattern} />
          ))}
        </div>

        {filteredPatterns.length === 0 && (
          <div className="text-center py-12 text-zinc-500">
            No patterns match your search.
          </div>
        )}
      </main>

      <TransportBar />
    </div>
  );
}

export default App;
