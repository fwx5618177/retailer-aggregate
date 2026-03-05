import { useFilterStore } from "@/store/filterStore";
import { Platform, MatchStatus } from "@/api/types";
import {
  SORT_OPTIONS,
  MATCH_STATUS_LABELS,
} from "@/utils/constants";

export function TopItemsFilters() {
  const {
    platform,
    brand,
    priceMin,
    priceMax,
    sort,
    matchStatus,
    setPlatform,
    setBrand,
    setPriceMin,
    setPriceMax,
    setSort,
    setMatchStatus,
    reset,
  } = useFilterStore();

  return (
    <div className="card">
      <div className="flex flex-wrap items-end gap-4">
        {/* Platform */}
        <div className="min-w-[140px]">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Platform
          </label>
          <select
            className="select-field"
            value={platform ?? ""}
            onChange={(e) =>
              setPlatform(
                e.target.value ? (e.target.value as Platform) : undefined,
              )
            }
          >
            <option value="">All Platforms</option>
            <option value={Platform.TIKTOK}>TikTok Shop</option>
            <option value={Platform.SHOPEE}>Shopee</option>
          </select>
        </div>

        {/* Brand */}
        <div className="min-w-[160px]">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Brand
          </label>
          <input
            type="text"
            className="input-field"
            placeholder="Search brand..."
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
          />
        </div>

        {/* Price Range */}
        <div className="flex items-end gap-2">
          <div className="w-24">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Price Min
            </label>
            <input
              type="number"
              className="input-field"
              placeholder="0"
              value={priceMin ?? ""}
              onChange={(e) =>
                setPriceMin(
                  e.target.value ? Number(e.target.value) : undefined,
                )
              }
            />
          </div>
          <span className="pb-2 text-slate-400">-</span>
          <div className="w-24">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Price Max
            </label>
            <input
              type="number"
              className="input-field"
              placeholder="999"
              value={priceMax ?? ""}
              onChange={(e) =>
                setPriceMax(
                  e.target.value ? Number(e.target.value) : undefined,
                )
              }
            />
          </div>
        </div>

        {/* Match Status */}
        <div className="min-w-[160px]">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Match Status
          </label>
          <select
            className="select-field"
            value={matchStatus ?? ""}
            onChange={(e) =>
              setMatchStatus(
                e.target.value ? (e.target.value as MatchStatus) : undefined,
              )
            }
          >
            <option value="">All Statuses</option>
            {Object.entries(MATCH_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Sort */}
        <div className="min-w-[160px]">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Sort By
          </label>
          <select
            className="select-field"
            value={sort}
            onChange={(e) =>
              setSort(e.target.value as typeof sort)
            }
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Reset */}
        <button className="btn-secondary" onClick={reset}>
          Reset
        </button>
      </div>
    </div>
  );
}
