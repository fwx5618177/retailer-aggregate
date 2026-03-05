import type { Alert } from "@/api/types";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatDate, humanize } from "@/utils/formatters";
import { ALERT_TYPE_LABELS } from "@/utils/constants";

interface AlertsListProps {
  alerts: Alert[];
  isLoading?: boolean;
}

function AlertTypeIcon({ type }: { type: string }) {
  switch (type) {
    case "rank_jump":
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
        </svg>
      );
    case "proxy_spike":
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
        </svg>
      );
    case "platform_gap":
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
        </svg>
      );
    case "price_anomaly":
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    default:
      return (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
      );
  }
}

const severityIconColors: Record<string, string> = {
  critical: "text-rose-500 bg-rose-50",
  high: "text-orange-500 bg-orange-50",
  medium: "text-amber-500 bg-amber-50",
  low: "text-sky-500 bg-sky-50",
};

function AlertCard({ alert }: { alert: Alert }) {
  const iconColor =
    severityIconColors[alert.severity] ?? "text-slate-500 bg-slate-50";

  // Parse description if it's a JSON string
  const parsedDescription = alert.description && alert.description.startsWith('{')
    ? (() => {
        try {
          return JSON.stringify(JSON.parse(alert.description), null, 2);
        } catch {
          return alert.description;
        }
      })()
    : alert.description;

  // Parse reasons if it's a string or use as object
  const parsedReasons = alert.reasons && typeof alert.reasons === 'string'
    ? (() => {
        try {
          return JSON.parse(alert.reasons);
        } catch {
          return {};
        }
      })()
    : alert.reasons || {};

  return (
    <div className="card transition-shadow hover:shadow-md">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${iconColor}`}
        >
          <AlertTypeIcon type={alert.alert_type} />
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <StatusBadge variant={alert.severity} />
            <StatusBadge
              variant={alert.alert_type}
              label={ALERT_TYPE_LABELS[alert.alert_type] ?? alert.alert_type}
            />
            <StatusBadge variant={alert.status} />
            {alert.platform && <StatusBadge variant={alert.platform} />}
          </div>

          <h4 className="mt-2 text-sm font-semibold text-slate-900">
            {alert.title}
          </h4>

          {parsedDescription && (
            <p className="mt-1 text-sm text-slate-600 font-mono text-xs whitespace-pre-wrap">{parsedDescription}</p>
          )}

          {/* Reasons */}
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
            {parsedReasons.trigger_metric && (
              <span>
                <span className="font-medium">Metric:</span>{" "}
                {humanize(parsedReasons.trigger_metric)}
              </span>
            )}
            {parsedReasons.old_value != null && (
              <span>
                <span className="font-medium">Old:</span>{" "}
                {parsedReasons.old_value}
              </span>
            )}
            {parsedReasons.new_value != null && (
              <span>
                <span className="font-medium">New:</span>{" "}
                {parsedReasons.new_value}
              </span>
            )}
            {parsedReasons.threshold != null && (
              <span>
                <span className="font-medium">Threshold:</span>{" "}
                {parsedReasons.threshold}
              </span>
            )}
          </div>

          {/* Suggested Action */}
          {alert.suggested_action && (
            <div className="mt-3 rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2">
              <p className="text-xs font-medium text-indigo-700">
                Suggested Action
              </p>
              <p className="mt-0.5 text-xs text-indigo-600">
                {alert.suggested_action}
              </p>
            </div>
          )}

          {/* Affected Items */}
          {alert.item_ids.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-slate-400">
                Affected items: {alert.item_ids.join(", ")}
              </p>
            </div>
          )}

          {/* Footer */}
          <div className="mt-2 text-xs text-slate-400">
            {formatDate(alert.event_date)}
            {alert.alert_id && ` | ${alert.alert_id}`}
          </div>
        </div>
      </div>
    </div>
  );
}

export function AlertsList({ alerts, isLoading = false }: AlertsListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="flex items-start gap-4">
              <div className="h-10 w-10 rounded-xl bg-slate-200" />
              <div className="flex-1 space-y-2">
                <div className="flex gap-2">
                  <div className="h-5 w-16 rounded bg-slate-200" />
                  <div className="h-5 w-20 rounded bg-slate-200" />
                </div>
                <div className="h-4 w-48 rounded bg-slate-200" />
                <div className="h-3 w-full rounded bg-slate-100" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="card text-center">
        <svg
          className="mx-auto h-12 w-12 text-slate-300"
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
        <p className="mt-2 text-sm text-slate-500">
          No alerts match your current filters.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {alerts.map((alert) => (
        <AlertCard key={alert.alert_id} alert={alert} />
      ))}
    </div>
  );
}
