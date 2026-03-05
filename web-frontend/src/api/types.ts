/* ─── Enums ─── */

export enum Platform {
  TIKTOK = "tiktok",
  SHOPEE = "shopee",
}

export enum MatchType {
  EXACT_SAME = "exact_same",
  VARIANT_FAMILY = "variant_family",
  SIMILAR = "similar",
  NO_MATCH = "no_match",
}

export enum MatchStatus {
  AUTO_ACCEPTED = "auto_accepted",
  NEEDS_REVIEW = "needs_review",
  NO_MATCH = "no_match",
  OVERRIDDEN = "overridden",
}

export enum OurStatus {
  COVERED = "covered",
  NOT_COVERED = "not_covered",
  HARVESTABLE = "harvestable",
  NOT_RECOMMENDED = "not_recommended",
}

export enum AlertType {
  RANK_JUMP = "rank_jump",
  PROXY_SPIKE = "proxy_spike",
  PLATFORM_GAP = "platform_gap",
  PRICE_ANOMALY = "price_anomaly",
}

export enum Severity {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

export enum AlertStatus {
  OPEN = "open",
  ACKNOWLEDGED = "acknowledged",
  RESOLVED = "resolved",
  DISMISSED = "dismissed",
}

export enum ProxyType {
  RANK = "rank",
  SOLD = "sold",
  SOLD_RANGE = "sold_range",
  REVIEW_COUNT = "review_count",
  LIKES = "likes",
  COMMENTS = "comments",
  RATING = "rating",
}

export enum ReviewDecision {
  ACCEPT = "accept",
  REJECT = "reject",
  CHANGE_TYPE = "change_type",
}

export enum DQStatus {
  PASSED = "passed",
  FAILED = "failed",
  DEGRADED = "degraded",
}

/* ─── Core Models ─── */

export interface TopItem {
  event_date: string;
  platform: Platform;
  item_id: string;
  title: string;
  category: string;
  rank: number;
  url?: string;
  brand_raw?: string;
  brand_std?: string;
  size_value?: number;
  size_unit?: string;
  pack_count?: number;
  image_url?: string;
  list_price?: number;
  promo_price?: number;
  currency?: string;
  review_count?: number;
  sold_range?: string;
  source_type?: "api" | "scrape" | "stub";
  ingested_at?: string;
  batch_id?: string;
  schema_version?: string;
}

export interface TopItemDetail extends TopItem {
  price_history?: Array<{
    event_date: string;
    list_price: number;
    promo_price?: number;
  }>;
  proxy_history?: Array<{
    event_date: string;
    proxy_type: string;
    proxy_value: string;
  }>;
  matches?: MatchResult[];
}

export interface PriceSnapshot {
  event_date: string;
  platform: Platform;
  item_id: string;
  list_price: number;
  promo_price?: number;
  promo_flag: boolean;
  currency: string;
  ingested_at?: string;
  batch_id?: string;
  schema_version?: string;
}

export interface SalesProxy {
  event_date: string;
  platform: Platform;
  item_id: string;
  proxy_type: ProxyType;
  proxy_value: string;
  proxy_numeric?: number;
  ingested_at?: string;
  batch_id?: string;
  schema_version?: string;
}

/* ─── Matching ─── */

export interface FieldAlignment {
  brand_match: boolean;
  brand_a?: string;
  brand_b?: string;
  spec_match: boolean;
  spec_a?: string;
  spec_b?: string;
  title_similarity: number;
  price_band_match: boolean;
}

export interface MatchReasons {
  strong_evidence: string[];
  weak_evidence: string[];
  field_alignment: FieldAlignment;
  missing_fields: string[];
}

export interface MatchResult {
  tiktok_item_id: string;
  shopee_item_id: string;
  tiktok_title?: string;
  shopee_title?: string;
  match_type: MatchType;
  confidence: number;
  status: MatchStatus;
  reasons: MatchReasons;
  rule_version?: string;
}

/* ─── Our Mapping ─── */

export interface OurMapping {
  platform: Platform;
  item_id: string;
  our_status: OurStatus;
  our_sku_id?: string;
  notes?: string;
  updated_by?: string;
  updated_at?: string;
  schema_version?: string;
}

export interface OurMappingRequest {
  our_status: OurStatus;
  our_sku_id?: string;
  notes?: string;
}

/* ─── Alerts ─── */

export interface AlertReasons {
  trigger_metric?: string;
  old_value?: string | number;
  new_value?: string | number;
  threshold?: string | number;
  context?: string;
}

export interface Alert {
  alert_id: string;
  event_date: string;
  platform?: Platform;
  item_ids: string[];
  alert_type: AlertType;
  severity: Severity;
  status: AlertStatus;
  title: string;
  description?: string;
  reasons?: AlertReasons | string;
  suggested_action?: string;
  batch_id?: string;
  schema_version?: string;
}

/* ─── Review ─── */

export interface ReviewQueueItem {
  tiktok_item_id: string;
  shopee_item_id: string;
  tiktok_item: TopItem;
  shopee_item: TopItem;
  match_type: MatchType;
  confidence: number;
  reasons: MatchReasons | string;
  rule_version?: string;
}

export interface ReviewDecisionRequest {
  decision: "accept" | "reject" | "change_type";
  new_match_type?: MatchType;
  comment?: string;
}

export interface ReviewDecisionResponse {
  decision_id: string;
  status: string;
  message: string;
}

/* ─── Overview ─── */

export interface OverviewResponse {
  event_date: string;
  window: string;
  top_n: number;
  category: string;
  platforms: string[];
  total_items: { tiktok: number; shopee: number };
  overlap: {
    exact_same: number;
    variant_family: number;
    similar: number;
    total_matched: number;
  };
  match_rate: number;
  needs_review_count: number;
  price_band_distribution: Array<{
    band: string;
    tiktok_count: number;
    shopee_count: number;
  }>;
  top_brands: Array<{
    brand: string;
    tiktok_count: number;
    shopee_count: number;
  }>;
  alerts_summary: {
    total: number;
    by_severity: Record<string, number>;
    by_type: Record<string, number>;
  };
  metadata: {
    schema_version: string;
    rule_version: string;
    batch_id: string;
    dq_status: string;
  };
}

/* ─── Pagination ─── */

export interface PagedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/* ─── Error ─── */

export interface ErrorResponse {
  error: string;
  message: string;
  request_id?: string;
  timestamp?: string;
}

/* ─── Query Parameter Types ─── */

export interface OverviewParams {
  category?: string;
  event_date?: string;
  window?: string;
}

export interface TopItemsParams {
  platform?: Platform;
  category?: string;
  event_date?: string;
  window?: string;
  brand?: string;
  price_min?: number;
  price_max?: number;
  sort?: "rank" | "price_asc" | "price_desc" | "title";
  match_status?: MatchStatus;
  limit?: number;
  offset?: number;
}

export interface AlertsParams {
  category?: string;
  event_date?: string;
  alert_type?: AlertType;
  severity?: Severity;
  status?: AlertStatus;
  limit?: number;
  offset?: number;
}

export interface ReviewQueueParams {
  category?: string;
  sort?: "confidence_asc" | "confidence_desc" | "date_desc";
  limit?: number;
  offset?: number;
}
