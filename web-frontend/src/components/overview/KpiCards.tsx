import { clsx } from "clsx";
import { formatNumber, formatPercent } from "@/utils/formatters";

interface KpiCardProps {
  label: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  color: "indigo" | "emerald" | "amber" | "rose" | "sky";
}

const colorMap = {
  indigo: {
    bg: "bg-indigo-50",
    icon: "text-indigo-600",
    ring: "ring-indigo-100",
  },
  emerald: {
    bg: "bg-emerald-50",
    icon: "text-emerald-600",
    ring: "ring-emerald-100",
  },
  amber: {
    bg: "bg-amber-50",
    icon: "text-amber-600",
    ring: "ring-amber-100",
  },
  rose: {
    bg: "bg-rose-50",
    icon: "text-rose-600",
    ring: "ring-rose-100",
  },
  sky: {
    bg: "bg-sky-50",
    icon: "text-sky-600",
    ring: "ring-sky-100",
  },
};

function KpiCard({ label, value, subtitle, icon, color }: KpiCardProps) {
  const colors = colorMap[color];

  return (
    <div className="card flex items-start gap-4">
      <div
        className={clsx(
          "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ring-1",
          colors.bg,
          colors.ring,
        )}
      >
        <div className={colors.icon}>{icon}</div>
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
        {subtitle && (
          <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>
        )}
      </div>
    </div>
  );
}

interface KpiCardsProps {
  totalTiktok?: number;
  totalShopee?: number;
  matchRate?: number;
  needsReviewCount?: number;
  isLoading?: boolean;
}

export function KpiCards({
  totalTiktok,
  totalShopee,
  matchRate,
  needsReviewCount,
  isLoading = false,
}: KpiCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="flex items-start gap-4">
              <div className="h-12 w-12 rounded-xl bg-slate-200" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-20 rounded bg-slate-200" />
                <div className="h-8 w-16 rounded bg-slate-200" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="TikTok Items"
        value={formatNumber(totalTiktok)}
        subtitle="Top selling products"
        color="rose"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
          </svg>
        }
      />
      <KpiCard
        label="Shopee Items"
        value={formatNumber(totalShopee)}
        subtitle="Top selling products"
        color="sky"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
          </svg>
        }
      />
      <KpiCard
        label="Match Rate"
        value={formatPercent(matchRate)}
        subtitle="Cross-platform matches"
        color="emerald"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
          </svg>
        }
      />
      <KpiCard
        label="Needs Review"
        value={formatNumber(needsReviewCount)}
        subtitle="Awaiting human review"
        color="amber"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        }
      />
    </div>
  );
}
