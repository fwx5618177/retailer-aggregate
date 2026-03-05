import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useFilterStore } from "@/store/filterStore";
import { useTopItems } from "@/hooks/useTopItems";
import { TopItemsFilters } from "@/components/top-items/TopItemsFilters";
import { TopItemsTable } from "@/components/top-items/TopItemsTable";
import { Pagination } from "@/components/shared/Pagination";
import { DEFAULT_PAGE_SIZE } from "@/utils/constants";
import type { TopItem } from "@/api/types";

export function TopItemsPage() {
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);

  const {
    platform,
    category,
    eventDate,
    window: windowPeriod,
    brand,
    priceMin,
    priceMax,
    sort,
    matchStatus,
  } = useFilterStore();

  const { data, isLoading, isError, error } = useTopItems({
    platform: platform || undefined,
    category: category || undefined,
    event_date: eventDate || undefined,
    window: windowPeriod || undefined,
    brand: brand || undefined,
    price_min: priceMin,
    price_max: priceMax,
    sort,
    match_status: matchStatus,
    limit: DEFAULT_PAGE_SIZE,
    offset,
  });

  const handleRowClick = useCallback(
    (item: TopItem) => {
      navigate(`/items/${item.platform}/${item.item_id}`);
    },
    [navigate],
  );

  const handlePrevious = useCallback(() => {
    setOffset((prev) => Math.max(0, prev - DEFAULT_PAGE_SIZE));
  }, []);

  const handleNext = useCallback(() => {
    setOffset((prev) => prev + DEFAULT_PAGE_SIZE);
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Top Items</h1>
        <p className="mt-1 text-sm text-slate-500">
          Browse and filter top-selling items across platforms
        </p>
      </div>

      {/* Filters */}
      <TopItemsFilters />

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4">
          <p className="text-sm text-rose-700">
            Failed to load items:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* Table */}
      <TopItemsTable
        items={data?.items ?? []}
        isLoading={isLoading}
        onRowClick={handleRowClick}
      />

      {/* Pagination */}
      {data && (
        <Pagination
          total={data.total}
          limit={data.limit}
          offset={data.offset}
          hasMore={data.has_more}
          onPrevious={handlePrevious}
          onNext={handleNext}
        />
      )}
    </div>
  );
}
