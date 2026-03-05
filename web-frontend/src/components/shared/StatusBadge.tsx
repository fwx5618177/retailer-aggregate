import { clsx } from "clsx";

type Variant =
  | "auto_accepted"
  | "needs_review"
  | "no_match"
  | "overridden"
  | "exact_same"
  | "variant_family"
  | "similar"
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "open"
  | "acknowledged"
  | "resolved"
  | "dismissed"
  | "covered"
  | "not_covered"
  | "harvestable"
  | "not_recommended"
  | "tiktok"
  | "shopee";

const variantClasses: Record<Variant, string> = {
  // Match statuses
  auto_accepted:
    "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  needs_review:
    "bg-amber-50 text-amber-700 ring-amber-600/20",
  no_match:
    "bg-slate-100 text-slate-600 ring-slate-500/20",
  overridden:
    "bg-indigo-50 text-indigo-700 ring-indigo-600/20",

  // Match types
  exact_same:
    "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  variant_family:
    "bg-sky-50 text-sky-700 ring-sky-600/20",
  similar:
    "bg-violet-50 text-violet-700 ring-violet-600/20",

  // Alert severity
  critical:
    "bg-rose-50 text-rose-700 ring-rose-600/20",
  high:
    "bg-orange-50 text-orange-700 ring-orange-600/20",
  medium:
    "bg-amber-50 text-amber-700 ring-amber-600/20",
  low:
    "bg-sky-50 text-sky-700 ring-sky-600/20",

  // Alert status
  open:
    "bg-rose-50 text-rose-700 ring-rose-600/20",
  acknowledged:
    "bg-amber-50 text-amber-700 ring-amber-600/20",
  resolved:
    "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  dismissed:
    "bg-slate-100 text-slate-600 ring-slate-500/20",

  // Our status
  covered:
    "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  not_covered:
    "bg-slate-100 text-slate-600 ring-slate-500/20",
  harvestable:
    "bg-amber-50 text-amber-700 ring-amber-600/20",
  not_recommended:
    "bg-rose-50 text-rose-700 ring-rose-600/20",

  // Platforms
  tiktok: "bg-gray-900 text-white ring-gray-900/20",
  shopee: "bg-orange-500 text-white ring-orange-500/20",
};

interface StatusBadgeProps {
  variant: string;
  label?: string;
  className?: string;
}

export function StatusBadge({ variant, label, className }: StatusBadgeProps) {
  const displayLabel =
    label ??
    variant
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());

  const colors =
    variantClasses[variant as Variant] ??
    "bg-slate-100 text-slate-600 ring-slate-500/20";

  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
        colors,
        className,
      )}
    >
      {displayLabel}
    </span>
  );
}
