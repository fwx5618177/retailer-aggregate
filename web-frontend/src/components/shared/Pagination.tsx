import { clsx } from "clsx";

interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export function Pagination({
  total,
  limit,
  offset,
  hasMore,
  onPrevious,
  onNext,
}: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);
  const showingFrom = total === 0 ? 0 : offset + 1;
  const showingTo = Math.min(offset + limit, total);

  return (
    <div className="flex items-center justify-between border-t border-slate-200 bg-white px-4 py-3">
      <div className="text-sm text-slate-500">
        Showing{" "}
        <span className="font-medium text-slate-700">{showingFrom}</span> to{" "}
        <span className="font-medium text-slate-700">{showingTo}</span> of{" "}
        <span className="font-medium text-slate-700">{total}</span> results
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-500">
          Page {currentPage} of {totalPages || 1}
        </span>

        <button
          onClick={onPrevious}
          disabled={offset === 0}
          className={clsx(
            "inline-flex items-center rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium transition-colors",
            offset === 0
              ? "cursor-not-allowed bg-slate-50 text-slate-300"
              : "bg-white text-slate-700 hover:bg-slate-50",
          )}
        >
          <svg
            className="mr-1 h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Previous
        </button>

        <button
          onClick={onNext}
          disabled={!hasMore}
          className={clsx(
            "inline-flex items-center rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium transition-colors",
            !hasMore
              ? "cursor-not-allowed bg-slate-50 text-slate-300"
              : "bg-white text-slate-700 hover:bg-slate-50",
          )}
        >
          Next
          <svg
            className="ml-1 h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
