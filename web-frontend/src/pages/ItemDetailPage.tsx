import { useParams, useNavigate } from "react-router-dom";
import { useItemDetail } from "@/hooks/useItemDetail";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { MetadataBar } from "@/components/shared/MetadataBar";
import { formatPrice, formatDate, formatPercent } from "@/utils/formatters";
import { PLATFORM_LABELS } from "@/utils/constants";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { MatchResult } from "@/api/types";

function MatchResultCard({ match }: { match: MatchResult }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusBadge variant={match.match_type} />
          <StatusBadge variant={match.status} />
        </div>
        <div className="text-right">
          <span className="text-sm text-slate-500">Confidence</span>
          <p className="text-lg font-bold text-slate-900">
            {formatPercent(match.confidence)}
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-6">
        <div>
          <p className="text-xs font-semibold uppercase text-slate-400">
            TikTok Item
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800">
            {match.tiktok_title ?? match.tiktok_item_id}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            ID: {match.tiktok_item_id}
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-slate-400">
            Shopee Item
          </p>
          <p className="mt-1 text-sm font-medium text-slate-800">
            {match.shopee_title ?? match.shopee_item_id}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            ID: {match.shopee_item_id}
          </p>
        </div>
      </div>

      {/* Reasons */}
      {match.reasons && (
        <div className="mt-4 space-y-2">
          {match.reasons.strong_evidence.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-emerald-700">
                Strong Evidence
              </p>
              <ul className="mt-1 space-y-0.5">
                {match.reasons.strong_evidence.map((ev, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-1.5 text-xs text-emerald-600"
                  >
                    <svg
                      className="mt-0.5 h-3 w-3 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    {ev}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {match.reasons.weak_evidence.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-amber-700">
                Weak Evidence
              </p>
              <ul className="mt-1 space-y-0.5">
                {match.reasons.weak_evidence.map((ev, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-1.5 text-xs text-amber-600"
                  >
                    <svg
                      className="mt-0.5 h-3 w-3 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    {ev}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Field Alignment */}
          <div className="mt-2 rounded-lg border border-slate-100 bg-slate-50 p-3">
            <p className="mb-2 text-xs font-semibold text-slate-600">
              Field Alignment
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1.5">
                <span
                  className={
                    match.reasons.field_alignment.brand_match
                      ? "text-emerald-500"
                      : "text-rose-500"
                  }
                >
                  {match.reasons.field_alignment.brand_match ? "Yes" : "No"}
                </span>
                <span className="text-slate-500">Brand Match</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span
                  className={
                    match.reasons.field_alignment.spec_match
                      ? "text-emerald-500"
                      : "text-rose-500"
                  }
                >
                  {match.reasons.field_alignment.spec_match ? "Yes" : "No"}
                </span>
                <span className="text-slate-500">Spec Match</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span
                  className={
                    match.reasons.field_alignment.price_band_match
                      ? "text-emerald-500"
                      : "text-rose-500"
                  }
                >
                  {match.reasons.field_alignment.price_band_match
                    ? "Yes"
                    : "No"}
                </span>
                <span className="text-slate-500">Price Band</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-slate-700">
                  {formatPercent(
                    match.reasons.field_alignment.title_similarity,
                  )}
                </span>
                <span className="text-slate-500">Title Similarity</span>
              </div>
            </div>
          </div>

          {match.reasons.missing_fields.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500">
                Missing Fields
              </p>
              <p className="mt-0.5 text-xs text-slate-400">
                {match.reasons.missing_fields.join(", ")}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ItemDetailPage() {
  const { platform, itemId } = useParams<{
    platform: string;
    itemId: string;
  }>();
  const navigate = useNavigate();

  const { data: item, isLoading, isError, error } = useItemDetail(
    platform ?? "",
    itemId ?? "",
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-slate-200" />
        <div className="card animate-pulse space-y-4">
          <div className="h-6 w-64 rounded bg-slate-200" />
          <div className="h-4 w-96 rounded bg-slate-200" />
          <div className="h-32 rounded bg-slate-100" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => navigate(-1)}
          className="btn-secondary"
        >
          &larr; Back
        </button>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-center">
          <p className="text-sm text-rose-700">
            Failed to load item detail:{" "}
            {error instanceof Error ? error.message : "Item not found"}
          </p>
        </div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => navigate(-1)}
          className="btn-secondary"
        >
          &larr; Back
        </button>
        <div className="card text-center text-sm text-slate-500">
          Item not found.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="btn-secondary"
      >
        &larr; Back to items
      </button>

      {/* Item Info Card */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <StatusBadge variant={item.platform} />
              <span className="text-sm text-slate-500">
                Rank #{item.rank}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">{item.title}</h1>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
              <span>
                <span className="text-slate-400">Brand:</span>{" "}
                {item.brand_std ?? item.brand_raw ?? "N/A"}
              </span>
              <span>
                <span className="text-slate-400">Category:</span>{" "}
                {item.category}
              </span>
              {item.size_value != null && (
                <span>
                  <span className="text-slate-400">Size:</span>{" "}
                  {item.size_value}
                  {item.size_unit}
                  {item.pack_count && item.pack_count > 1
                    ? ` x${item.pack_count}`
                    : ""}
                </span>
              )}
              <span>
                <span className="text-slate-400">Sold:</span>{" "}
                {item.sold_range ?? "N/A"}
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-slate-900">
              {formatPrice(
                item.promo_price ?? item.list_price,
                item.currency,
              )}
            </p>
            {item.promo_price != null &&
              item.list_price != null &&
              item.promo_price < item.list_price && (
                <p className="text-sm text-slate-400 line-through">
                  {formatPrice(item.list_price, item.currency)}
                </p>
              )}
          </div>
        </div>
        {item.url && (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block text-sm text-primary-600 hover:text-primary-700 hover:underline"
          >
            View on{" "}
            {PLATFORM_LABELS[item.platform] ?? item.platform} &rarr;
          </a>
        )}
      </div>

      {/* Price History Chart */}
      {item.price_history && item.price_history.length > 0 && (
        <div className="card">
          <h2 className="mb-4 text-base font-semibold text-slate-800">
            Price History
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={item.price_history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="event_date"
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={(v: string) => formatDate(v)}
              />
              <YAxis
                tick={{ fontSize: 12, fill: "#64748b" }}
                tickFormatter={(v: number) =>
                  `${(v / 100).toFixed(0)}`
                }
              />
              <Tooltip
                formatter={(value: number) => [
                  formatPrice(value, item.currency),
                ]}
                labelFormatter={(label: string) => formatDate(label)}
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e2e8f0",
                }}
              />
              <Line
                type="monotone"
                dataKey="list_price"
                name="List Price"
                stroke="#6366f1"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="promo_price"
                name="Promo Price"
                stroke="#f43f5e"
                strokeWidth={2}
                dot={{ r: 3 }}
                strokeDasharray="4 4"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Matches */}
      <div>
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Cross-Platform Matches
          {item.matches && (
            <span className="ml-2 text-sm font-normal text-slate-500">
              ({item.matches.length})
            </span>
          )}
        </h2>
        {item.matches && item.matches.length > 0 ? (
          <div className="space-y-4">
            {item.matches.map((match, i) => (
              <MatchResultCard key={i} match={match} />
            ))}
          </div>
        ) : (
          <div className="card text-center text-sm text-slate-400">
            No cross-platform matches found for this item.
          </div>
        )}
      </div>

      {/* Metadata */}
      <MetadataBar
        eventDate={item.event_date}
        schemaVersion={item.schema_version}
        batchId={item.batch_id}
      />
    </div>
  );
}
