import { useState } from "react";
import { useAlerts } from "@/hooks/useAlerts";
import { AlertsList } from "@/components/alerts/AlertsList";
import { Pagination } from "@/components/shared/Pagination";
import { DEFAULT_PAGE_SIZE } from "@/utils/constants";
import { useFilterStore } from "@/store/filterStore";
import type { AlertType, Severity, AlertStatus } from "@/api/types";
import {
  ALERT_TYPE_LABELS,
  SEVERITY_LABELS,
} from "@/utils/constants";

const ALERT_STATUS_OPTIONS: { value: AlertStatus; label: string }[] = [
  { value: "open" as AlertStatus, label: "Open" },
  { value: "acknowledged" as AlertStatus, label: "Acknowledged" },
  { value: "resolved" as AlertStatus, label: "Resolved" },
  { value: "dismissed" as AlertStatus, label: "Dismissed" },
];

export function AlertsPage() {
  const { category, eventDate } = useFilterStore();
  const [alertType, setAlertType] = useState<AlertType | undefined>();
  const [severity, setSeverity] = useState<Severity | undefined>();
  const [status, setStatus] = useState<AlertStatus | undefined>();
  const [offset, setOffset] = useState(0);

  const { data, isLoading, isError, error } = useAlerts({
    category: category || undefined,
    event_date: eventDate || undefined,
    alert_type: alertType,
    severity,
    status,
    limit: DEFAULT_PAGE_SIZE,
    offset,
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
        <p className="mt-1 text-sm text-slate-500">
          Monitor competitive intelligence signals and opportunities
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-end gap-4">
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Alert Type
            </label>
            <select
              className="select-field"
              value={alertType ?? ""}
              onChange={(e) =>
                setAlertType(
                  e.target.value ? (e.target.value as AlertType) : undefined,
                )
              }
            >
              <option value="">All Types</option>
              {Object.entries(ALERT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-[140px]">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Severity
            </label>
            <select
              className="select-field"
              value={severity ?? ""}
              onChange={(e) =>
                setSeverity(
                  e.target.value ? (e.target.value as Severity) : undefined,
                )
              }
            >
              <option value="">All Severities</option>
              {Object.entries(SEVERITY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-[140px]">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Status
            </label>
            <select
              className="select-field"
              value={status ?? ""}
              onChange={(e) =>
                setStatus(
                  e.target.value ? (e.target.value as AlertStatus) : undefined,
                )
              }
            >
              <option value="">All Statuses</option>
              {ALERT_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <button
            className="btn-secondary"
            onClick={() => {
              setAlertType(undefined);
              setSeverity(undefined);
              setStatus(undefined);
              setOffset(0);
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4">
          <p className="text-sm text-rose-700">
            Failed to load alerts:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* Results count */}
      {data && !isLoading && (
        <p className="text-sm text-slate-500">
          {data.total} alert{data.total !== 1 ? "s" : ""} found
        </p>
      )}

      {/* Alerts List */}
      <AlertsList alerts={data?.items ?? []} isLoading={isLoading} />

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
