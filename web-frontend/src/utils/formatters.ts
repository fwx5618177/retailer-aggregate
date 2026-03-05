import dayjs from "dayjs";

/**
 * Format a price amount into a locale-appropriate currency string.
 * The API stores prices in the smallest currency unit (satang for THB),
 * so we divide by 100 for display.
 */
export function formatPrice(
  amount: number | undefined | null,
  currency = "THB",
): string {
  if (amount == null) return "N/A";

  const value = amount / 100;

  if (currency === "THB") {
    return `฿${value.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(value);
}

/** Format an ISO date string into a short date. */
export function formatDate(date: string | undefined | null): string {
  if (!date) return "N/A";
  return dayjs(date).format("YYYY-MM-DD");
}

/** Format a number with thousands separators. */
export function formatNumber(n: number | undefined | null): string {
  if (n == null) return "N/A";
  return n.toLocaleString("en-US");
}

/** Format a decimal (0-1) or whole number as a percentage. */
export function formatPercent(n: number | undefined | null): string {
  if (n == null) return "N/A";

  // If value is <= 1, treat as a fraction and multiply by 100
  const pct = n <= 1 ? n * 100 : n;

  return `${pct.toFixed(1)}%`;
}

/** Truncate a string with an ellipsis if it exceeds max length. */
export function truncate(str: string, maxLength = 60): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 1) + "\u2026";
}

/** Capitalise the first letter and replace underscores with spaces. */
export function humanize(str: string): string {
  return str
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
