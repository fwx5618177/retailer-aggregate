import { formatDate } from "@/utils/formatters";

interface MetadataBarProps {
  eventDate?: string;
  window?: string;
  topN?: number;
  ruleVersion?: string;
  schemaVersion?: string;
  batchId?: string;
  dqStatus?: string;
}

export function MetadataBar({
  eventDate,
  window: windowPeriod,
  topN,
  ruleVersion,
  schemaVersion,
  batchId,
  dqStatus,
}: MetadataBarProps) {
  const items = [
    { label: "Event Date", value: formatDate(eventDate) },
    { label: "Window", value: windowPeriod },
    { label: "Top N", value: topN?.toString() },
    { label: "Rule Version", value: ruleVersion },
    { label: "Schema Version", value: schemaVersion },
    { label: "Batch", value: batchId ? batchId.slice(0, 8) + "\u2026" : undefined },
    { label: "DQ Status", value: dqStatus },
  ].filter((item) => item.value != null);

  if (items.length === 0) return null;

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-slate-500">
        {items.map((item) => (
          <span key={item.label}>
            <span className="font-medium text-slate-600">{item.label}:</span>{" "}
            <span
              className={
                item.label === "DQ Status" && item.value === "degraded"
                  ? "font-semibold text-amber-600"
                  : item.label === "DQ Status" && item.value === "failed"
                    ? "font-semibold text-rose-600"
                    : ""
              }
            >
              {item.value}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
