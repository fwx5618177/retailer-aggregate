export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const DEFAULT_PAGE_SIZE = 20;

export const DEFAULT_WINDOW = "14d";

export const DEFAULT_CATEGORY = "personal_care";

export const WINDOW_OPTIONS = [
  { value: "7d", label: "7 Days" },
  { value: "14d", label: "14 Days" },
  { value: "30d", label: "30 Days" },
] as const;

export const SORT_OPTIONS = [
  { value: "rank", label: "Rank" },
  { value: "price_asc", label: "Price (Low to High)" },
  { value: "price_desc", label: "Price (High to Low)" },
  { value: "title", label: "Title (A-Z)" },
] as const;

export const REVIEW_SORT_OPTIONS = [
  { value: "confidence_desc", label: "Confidence (High to Low)" },
  { value: "confidence_asc", label: "Confidence (Low to High)" },
  { value: "date_desc", label: "Date (Newest)" },
] as const;

export const PLATFORM_LABELS: Record<string, string> = {
  tiktok: "TikTok Shop",
  shopee: "Shopee",
};

export const MATCH_TYPE_LABELS: Record<string, string> = {
  exact_same: "Exact Same",
  variant_family: "Variant Family",
  similar: "Similar",
  no_match: "No Match",
};

export const MATCH_STATUS_LABELS: Record<string, string> = {
  auto_accepted: "Auto Accepted",
  needs_review: "Needs Review",
  no_match: "No Match",
  overridden: "Overridden",
};

export const ALERT_TYPE_LABELS: Record<string, string> = {
  rank_jump: "Rank Jump",
  proxy_spike: "Proxy Spike",
  platform_gap: "Platform Gap",
  price_anomaly: "Price Anomaly",
};

export const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export const OUR_STATUS_LABELS: Record<string, string> = {
  covered: "Covered",
  not_covered: "Not Covered",
  harvestable: "Harvestable",
  not_recommended: "Not Recommended",
};
