import { useState, useCallback } from "react";
import { useReviewQueue, useSubmitDecision } from "@/hooks/useReviewQueue";
import { ReviewQueue } from "@/components/review/ReviewQueue";
import { Pagination } from "@/components/shared/Pagination";
import { DEFAULT_PAGE_SIZE, REVIEW_SORT_OPTIONS } from "@/utils/constants";
import type { ReviewDecisionRequest, ReviewQueueParams } from "@/api/types";

export function ReviewPage() {
  const [offset, setOffset] = useState(0);
  const [sort, setSort] = useState<ReviewQueueParams["sort"]>("confidence_desc");

  const { data, isLoading, isError, error } = useReviewQueue({
    sort,
    limit: DEFAULT_PAGE_SIZE,
    offset,
  });

  const submitMutation = useSubmitDecision();

  const handleSubmitDecision = useCallback(
    (
      tiktokItemId: string,
      shopeeItemId: string,
      request: ReviewDecisionRequest,
    ) => {
      submitMutation.mutate({ tiktokItemId, shopeeItemId, request });
    },
    [submitMutation],
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Review Queue</h1>
            <p className="mt-1 text-sm text-slate-500">
              Review and decide on cross-platform item matches
            </p>
          </div>
          {data && (
            <span className="flex h-7 min-w-[28px] items-center justify-center rounded-full bg-amber-100 px-2 text-xs font-bold text-amber-700">
              {data.total}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-600">Sort by</label>
          <select
            className="select-field w-48"
            value={sort}
            onChange={(e) => {
              setSort(e.target.value as ReviewQueueParams["sort"]);
              setOffset(0);
            }}
          >
            {REVIEW_SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Success message */}
      {submitMutation.isSuccess && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-sm text-emerald-700">
            Decision recorded successfully.
          </p>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4">
          <p className="text-sm text-rose-700">
            Failed to load review queue:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {submitMutation.isError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4">
          <p className="text-sm text-rose-700">
            Failed to submit decision:{" "}
            {submitMutation.error instanceof Error
              ? submitMutation.error.message
              : "Unknown error"}
          </p>
        </div>
      )}

      {/* Queue */}
      <ReviewQueue
        items={data?.items ?? []}
        isLoading={isLoading}
        onSubmitDecision={handleSubmitDecision}
        isSubmitting={submitMutation.isPending}
      />

      {/* Pagination */}
      {data && (
        <Pagination
          total={data.total}
          limit={data.limit}
          offset={data.offset}
          hasMore={data.has_more}
          onPrevious={() =>
            setOffset((prev) => Math.max(0, prev - DEFAULT_PAGE_SIZE))
          }
          onNext={() => setOffset((prev) => prev + DEFAULT_PAGE_SIZE)}
        />
      )}
    </div>
  );
}
