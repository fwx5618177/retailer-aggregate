import type { ReviewQueueItem, ReviewDecisionRequest } from "@/api/types";
import { ReviewPairCard } from "./ReviewPairCard";

interface ReviewQueueProps {
  items: ReviewQueueItem[];
  isLoading?: boolean;
  onSubmitDecision: (
    tiktokItemId: string,
    shopeeItemId: string,
    request: ReviewDecisionRequest,
  ) => void;
  isSubmitting?: boolean;
}

export function ReviewQueue({
  items,
  isLoading = false,
  onSubmitDecision,
  isSubmitting = false,
}: ReviewQueueProps) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="card animate-pulse space-y-4">
            <div className="flex items-center gap-2">
              <div className="h-5 w-20 rounded bg-slate-200" />
              <div className="h-5 w-16 rounded bg-slate-200" />
            </div>
            <div className="flex gap-6">
              <div className="flex-1 space-y-2">
                <div className="h-4 w-32 rounded bg-slate-200" />
                <div className="h-12 rounded bg-slate-100" />
              </div>
              <div className="w-px bg-slate-200" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-32 rounded bg-slate-200" />
                <div className="h-12 rounded bg-slate-100" />
              </div>
            </div>
            <div className="h-32 rounded bg-slate-100" />
          </div>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="card text-center">
        <svg
          className="mx-auto h-12 w-12 text-emerald-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="mt-3 text-sm font-medium text-slate-700">
          All caught up!
        </p>
        <p className="mt-1 text-sm text-slate-500">
          No items pending review at this time.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {items.map((pair) => (
        <ReviewPairCard
          key={`${pair.tiktok_item_id}-${pair.shopee_item_id}`}
          pair={pair}
          onSubmitDecision={onSubmitDecision}
          isSubmitting={isSubmitting}
        />
      ))}
    </div>
  );
}
