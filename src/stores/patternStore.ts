import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { SlonimskyPattern, PatternCategory } from "@/core/types";
import { generateCatalog } from "@/core/pattern";

interface PatternFilters {
  category: PatternCategory | "all";
  interpolationType: "all" | "none" | "ascending" | "descending";
  hasUltrapolation: "all" | "yes" | "no";
  searchQuery: string;
}

interface PatternStore {
  catalog: SlonimskyPattern[];
  selectedPattern: SlonimskyPattern | null;
  filters: PatternFilters;
  masteredPatternIds: string[];
  
  filteredPatterns: () => SlonimskyPattern[];
  selectPattern: (pattern: SlonimskyPattern | null) => void;
  setFilter: <K extends keyof PatternFilters>(
    key: K,
    value: PatternFilters[K]
  ) => void;
  resetFilters: () => void;
  toggleMastered: (patternId: string) => void;
  isMastered: (patternId: string) => boolean;
  getMasteredCount: () => number;
  selectRandomPattern: () => void;
  selectNextPattern: () => void;
  selectPreviousPattern: () => void;
}

const defaultFilters: PatternFilters = {
  category: "all",
  interpolationType: "all",
  hasUltrapolation: "all",
  searchQuery: "",
};

export const usePatternStore = create<PatternStore>()(
  persist(
    (set, get) => ({
      catalog: generateCatalog(),
      selectedPattern: null,
      filters: defaultFilters,
      masteredPatternIds: [],

      filteredPatterns: () => {
        const { catalog, filters } = get();

        return catalog.filter((pattern) => {
          if (filters.category !== "all" && pattern.category !== filters.category) {
            return false;
          }

          if (filters.interpolationType !== "all" && pattern.interpolation.type !== filters.interpolationType) {
            return false;
          }

          if (filters.hasUltrapolation === "yes" && pattern.ultrapolation.type === "none") {
            return false;
          }
          if (filters.hasUltrapolation === "no" && pattern.ultrapolation.type !== "none") {
            return false;
          }

          if (filters.searchQuery) {
            const query = filters.searchQuery.toLowerCase();
            const matchesName = pattern.name.toLowerCase().includes(query);
            const matchesId = pattern.id.toLowerCase().includes(query);
            if (!matchesName && !matchesId) {
              return false;
            }
          }

          return true;
        });
      },

      selectPattern: (pattern) => set({ selectedPattern: pattern }),

      setFilter: (key, value) =>
        set((state) => ({
          filters: { ...state.filters, [key]: value },
        })),

      resetFilters: () => set({ filters: defaultFilters }),

      toggleMastered: (patternId) =>
        set((state) => {
          const ids = state.masteredPatternIds;
          const isCurrentlyMastered = ids.includes(patternId);
          return {
            masteredPatternIds: isCurrentlyMastered
              ? ids.filter((id) => id !== patternId)
              : [...ids, patternId],
          };
        }),

      isMastered: (patternId) => get().masteredPatternIds.includes(patternId),

      getMasteredCount: () => get().masteredPatternIds.length,

      selectRandomPattern: () => {
        const patterns = get().filteredPatterns();
        if (patterns.length === 0) return;
        const randomIndex = Math.floor(Math.random() * patterns.length);
        set({ selectedPattern: patterns[randomIndex] });
      },

      selectNextPattern: () => {
        const patterns = get().filteredPatterns();
        const current = get().selectedPattern;
        if (patterns.length === 0) return;
        
        if (!current) {
          set({ selectedPattern: patterns[0] });
          return;
        }
        
        const currentIndex = patterns.findIndex((p) => p.id === current.id);
        const nextIndex = (currentIndex + 1) % patterns.length;
        set({ selectedPattern: patterns[nextIndex] });
      },

      selectPreviousPattern: () => {
        const patterns = get().filteredPatterns();
        const current = get().selectedPattern;
        if (patterns.length === 0) return;
        
        if (!current) {
          set({ selectedPattern: patterns[patterns.length - 1] });
          return;
        }
        
        const currentIndex = patterns.findIndex((p) => p.id === current.id);
        const prevIndex = currentIndex <= 0 ? patterns.length - 1 : currentIndex - 1;
        set({ selectedPattern: patterns[prevIndex] });
      },
    }),
    {
      name: "slonimsky-patterns",
      partialize: (state) => ({
        filters: {
          category: state.filters.category,
          interpolationType: state.filters.interpolationType,
          hasUltrapolation: state.filters.hasUltrapolation,
        },
        masteredPatternIds: state.masteredPatternIds,
      }),
    }
  )
);
