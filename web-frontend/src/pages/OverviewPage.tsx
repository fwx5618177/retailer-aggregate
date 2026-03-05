import { useFilterStore } from "@/store/filterStore";
import { useOverview } from "@/hooks/useOverview";
import { KpiCards } from "@/components/overview/KpiCards";
import { OverlapChart } from "@/components/overview/OverlapChart";
import { PriceBandChart } from "@/components/overview/PriceBandChart";
import { TrendChart } from "@/components/overview/TrendChart";
import { MetadataBar } from "@/components/shared/MetadataBar";
import { DegradedBanner } from "@/components/shared/DegradedBanner";
import { WINDOW_OPTIONS } from "@/utils/constants";
import { humanize } from "@/utils/formatters";

export function OverviewPage() {
  const { category, eventDate, window: windowPeriod, setWindow } = useFilterStore();

  const { data, isLoading, isError, error } = useOverview({
    category: category || undefined,
    event_date: eventDate || undefined,
    window: windowPeriod || undefined,
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Overview</h1>
          <p className="mt-1 text-sm text-slate-500">
            Cross-platform competitive intelligence dashboard
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-600">Window</label>
          <select
            className="select-field w-32"
            value={windowPeriod}
            onChange={(e) => setWindow(e.target.value)}
          >
            {WINDOW_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* DQ Banner */}
      <DegradedBanner dqStatus={data?.metadata?.dq_status} />

      {/* Error state */}
      {isError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4">
          <p className="text-sm text-rose-700">
            Failed to load overview data:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* KPI Cards */}
      <KpiCards
        totalTiktok={data?.total_items?.tiktok}
        totalShopee={data?.total_items?.shopee}
        matchRate={data?.match_rate}
        needsReviewCount={data?.needs_review_count}
        isLoading={isLoading}
      />

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <OverlapChart overlap={data?.overlap} isLoading={isLoading} />
        <PriceBandChart
          data={data?.price_band_distribution}
          isLoading={isLoading}
        />
      </div>

      {/* Trend + Top Brands */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <TrendChart isLoading={isLoading} />

        {/* Top Brands Table */}
        <div className="card">
          <h3 className="mb-4 text-base font-semibold text-slate-800">
            Top Brands
          </h3>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex animate-pulse items-center gap-4">
                  <div className="h-4 w-24 rounded bg-slate-200" />
                  <div className="h-4 w-12 rounded bg-slate-200" />
                  <div className="h-4 w-12 rounded bg-slate-200" />
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold uppercase text-slate-500">
                      Brand
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-semibold uppercase text-slate-500">
                      TikTok
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-semibold uppercase text-slate-500">
                      Shopee
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data?.top_brands && data.top_brands.length > 0 ? (
                    data.top_brands.map((brand) => (
                      <tr key={brand.brand} className="hover:bg-slate-50">
                        <td className="px-4 py-2 text-sm font-medium text-slate-700">
                          {brand.brand}
                        </td>
                        <td className="px-4 py-2 text-right text-sm text-slate-600">
                          {brand.tiktok_count}
                        </td>
                        <td className="px-4 py-2 text-right text-sm text-slate-600">
                          {brand.shopee_count}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-4 py-8 text-center text-sm text-slate-400"
                      >
                        No brand data available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Alerts Summary */}
      <div className="card">
        <h3 className="mb-4 text-base font-semibold text-slate-800">
          Alerts Summary
        </h3>
        {isLoading ? (
          <div className="h-16 animate-pulse rounded bg-slate-100" />
        ) : data?.alerts_summary ? (
          <div className="flex flex-wrap gap-6">
            <div>
              <p className="text-sm text-slate-500">Total Alerts</p>
              <p className="text-xl font-bold text-slate-900">
                {data.alerts_summary.total}
              </p>
            </div>
            {Object.entries(data.alerts_summary.by_severity).map(
              ([severity, count]) => (
                <div key={severity}>
                  <p className="text-sm text-slate-500">
                    {humanize(severity)}
                  </p>
                  <p className="text-xl font-bold text-slate-900">{count}</p>
                </div>
              ),
            )}
            <div className="border-l border-slate-200 pl-6">
              {Object.entries(data.alerts_summary.by_type).map(
                ([type, count]) => (
                  <div key={type} className="flex items-center gap-2 text-sm">
                    <span className="text-slate-500">{humanize(type)}:</span>
                    <span className="font-medium text-slate-700">{count}</span>
                  </div>
                ),
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">No alerts data available.</p>
        )}
      </div>

      {/* Metadata Bar */}
      <MetadataBar
        eventDate={data?.event_date}
        window={data?.window}
        topN={data?.top_n}
        ruleVersion={data?.metadata?.rule_version}
        schemaVersion={data?.metadata?.schema_version}
        batchId={data?.metadata?.batch_id}
        dqStatus={data?.metadata?.dq_status}
      />
    </div>
  );
}
