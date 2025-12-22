import { create } from "zustand";
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
  
  filteredPatterns: () => SlonimskyPattern[];
  selectPattern: (pattern: SlonimskyPattern | null) => void;
  setFilter: <K extends keyof PatternFilters>(
    key: K,
    value: PatternFilters[K]
  ) => void;
  resetFilters: () => void;
}

const defaultFilters: PatternFilters = {
  category: "all",
  interpolationType: "all",
  hasUltrapolation: "all",
  searchQuery: "",
};

export const usePatternStore = create<PatternStore>((set, get) => ({
  catalog: generateCatalog(),
  selectedPattern: null,
  filters: defaultFilters,

  filteredPatterns: () => {
    const { catalog, filters } = get();

    return catalog.filter((pattern) => {
      if (
        filters.category !== "all" &&
        pattern.category !== filters.category
      ) {
        return false;
      }

      if (
        filters.interpolationType !== "all" &&
        pattern.interpolation.type !== filters.interpolationType
      ) {
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
}));
