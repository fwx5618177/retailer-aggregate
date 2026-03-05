import { create } from "zustand";
import type { MatchStatus, Platform } from "@/api/types";

export interface FilterState {
  platform: Platform | undefined;
  category: string;
  eventDate: string;
  window: string;
  brand: string;
  priceMin: number | undefined;
  priceMax: number | undefined;
  sort: "rank" | "price_asc" | "price_desc" | "title";
  matchStatus: MatchStatus | undefined;
}

interface FilterActions {
  setPlatform: (platform: Platform | undefined) => void;
  setCategory: (category: string) => void;
  setEventDate: (eventDate: string) => void;
  setWindow: (window: string) => void;
  setBrand: (brand: string) => void;
  setPriceMin: (priceMin: number | undefined) => void;
  setPriceMax: (priceMax: number | undefined) => void;
  setSort: (sort: FilterState["sort"]) => void;
  setMatchStatus: (matchStatus: MatchStatus | undefined) => void;
  reset: () => void;
}

const initialState: FilterState = {
  platform: undefined,
  category: "personal_care",
  eventDate: "",
  window: "14d",
  brand: "",
  priceMin: undefined,
  priceMax: undefined,
  sort: "rank",
  matchStatus: undefined,
};

export const useFilterStore = create<FilterState & FilterActions>((set) => ({
  ...initialState,

  setPlatform: (platform) => set({ platform }),
  setCategory: (category) => set({ category }),
  setEventDate: (eventDate) => set({ eventDate }),
  setWindow: (window) => set({ window }),
  setBrand: (brand) => set({ brand }),
  setPriceMin: (priceMin) => set({ priceMin }),
  setPriceMax: (priceMax) => set({ priceMax }),
  setSort: (sort) => set({ sort }),
  setMatchStatus: (matchStatus) => set({ matchStatus }),
  reset: () => set(initialState),
}));
