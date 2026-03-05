interface DegradedBannerProps {
  dqStatus?: string;
  message?: string;
}

export function DegradedBanner({
  dqStatus,
  message,
}: DegradedBannerProps) {
  if (dqStatus !== "degraded" && dqStatus !== "failed") return null;

  const isFailed = dqStatus === "failed";

  return (
    <div
      className={
        isFailed
          ? "rounded-lg border border-rose-200 bg-rose-50 p-4"
          : "rounded-lg border border-amber-200 bg-amber-50 p-4"
      }
    >
      <div className="flex items-center gap-3">
        <svg
          className={
            isFailed
              ? "h-5 w-5 shrink-0 text-rose-500"
              : "h-5 w-5 shrink-0 text-amber-500"
          }
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
        <div>
          <h4
            className={
              isFailed
                ? "text-sm font-semibold text-rose-800"
                : "text-sm font-semibold text-amber-800"
            }
          >
            {isFailed ? "Data Quality Failed" : "Data Quality Degraded"}
          </h4>
          <p
            className={
              isFailed
                ? "mt-0.5 text-sm text-rose-700"
                : "mt-0.5 text-sm text-amber-700"
            }
          >
            {message ??
              (isFailed
                ? "One or more data quality checks have failed. Data may be unreliable."
                : "Some data quality checks did not fully pass. Numbers may be approximate.")}
          </p>
        </div>
      </div>
    </div>
  );
}
