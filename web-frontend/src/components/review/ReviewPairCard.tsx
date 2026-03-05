import { useState } from "react";
import type { ReviewQueueItem, ReviewDecisionRequest } from "@/api/types";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ReasonsDisplay } from "./ReasonsDisplay";
import { DecisionForm } from "./DecisionForm";
import { formatPrice, formatPercent, truncate } from "@/utils/formatters";
import { clsx } from "clsx";

interface ReviewPairCardProps {
  pair: ReviewQueueItem;
  onSubmitDecision: (
    tiktokItemId: string,
    shopeeItemId: string,
    request: ReviewDecisionRequest,
  ) => void;
  isSubmitting?: boolean;
}

function ItemSide({
  label,
  platform,
  item,
}: {
  label: string;
  platform: "tiktok" | "shopee";
  item: ReviewQueueItem["tiktok_item"];
}) {
  return (
    <div className="flex-1 space-y-2">
      <div className="flex items-center gap-2">
        <StatusBadge variant={platform} />
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </span>
      </div>
      <h4 className="text-sm font-semibold text-slate-900">
        {truncate(item.title, 60)}
      </h4>
      <div className="space-y-1 text-xs text-slate-600">
        <p>
          <span className="text-slate-400">Brand:</span>{" "}
          {item.brand_std ?? item.brand_raw ?? "N/A"}
        </p>
        <p>
          <span className="text-slate-400">Spec:</span>{" "}
          {item.size_value != null
            ? `${item.size_value}${item.size_unit ?? ""}`
            : "N/A"}
          {item.pack_count != null && item.pack_count > 1
            ? ` x${item.pack_count}`
            : ""}
        </p>
        <p>
          <span className="text-slate-400">Price:</span>{" "}
          <span className="font-medium text-slate-700">
            {formatPrice(item.promo_price ?? item.list_price, item.currency)}
          </span>
        </p>
        <p>
          <span className="text-slate-400">Rank:</span> #{item.rank}
        </p>
        <p>
          <span className="text-slate-400">Sold:</span>{" "}
          {item.sold_range ?? "N/A"}
        </p>
      </div>
    </div>
  );
}

export function ReviewPairCard({
  pair,
  onSubmitDecision,
  isSubmitting = false,
}: ReviewPairCardProps) {
  const [expanded, setExpanded] = useState(false);

  const confidenceColor =
    pair.confidence >= 0.8
      ? "text-emerald-600"
      : pair.confidence >= 0.5
        ? "text-amber-600"
        : "text-rose-600";

  const confidenceBarWidth = `${Math.min(pair.confidence * 100, 100)}%`;
  const confidenceBarColor =
    pair.confidence >= 0.8
      ? "bg-emerald-500"
      : pair.confidence >= 0.5
        ? "bg-amber-500"
        : "bg-rose-500";

  return (
    <div className="card space-y-4">
      {/* Top row: match metadata */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusBadge variant={pair.match_type} />
          {pair.rule_version && (
            <span className="text-xs text-slate-400">
              rule {pair.rule_version}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-slate-400">Confidence</span>
            <p className={clsx("text-lg font-bold", confidenceColor)}>
              {formatPercent(pair.confidence)}
            </p>
          </div>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={clsx("h-full rounded-full transition-all", confidenceBarColor)}
          style={{ width: confidenceBarWidth }}
        />
      </div>

      {/* Side by side comparison */}
      <div className="flex gap-6">
        <ItemSide
          label="TikTok Item"
          platform="tiktok"
          item={pair.tiktok_item}
        />

        {/* Center divider */}
        <div className="flex flex-col items-center justify-center px-2">
          <div className="h-full w-px bg-slate-200" />
          <svg
            className="my-2 h-5 w-5 shrink-0 text-slate-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5"
            />
          </svg>
          <div className="h-full w-px bg-slate-200" />
        </div>

        <ItemSide
          label="Shopee Item"
          platform="shopee"
          item={pair.shopee_item}
        />
      </div>

      {/* Expand to show reasons */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-center gap-1 rounded-lg border border-slate-200 py-2 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700"
      >
        {expanded ? "Hide Details" : "Show Match Reasons"}
        <svg
          className={clsx(
            "h-4 w-4 transition-transform",
            expanded && "rotate-180",
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {expanded && (
        <div className="rounded-xl border border-slate-100 bg-white p-4">
          <ReasonsDisplay reasons={typeof pair.reasons === 'string' ? JSON.parse(pair.reasons) : pair.reasons} />
        </div>
      )}

      {/* Decision Form */}
      <DecisionForm
        tiktokItemId={pair.tiktok_item_id}
        shopeeItemId={pair.shopee_item_id}
        currentMatchType={pair.match_type}
        onSubmit={onSubmitDecision}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}
