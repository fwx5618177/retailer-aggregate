import type {
  AlertStatus,
  AlertType,
  DQStatus,
  MatchStatus,
  MatchType,
  OurStatus,
  Platform,
  ProxyType,
  Severity,
} from "./enums";

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

export interface MatchMapPlatform {
  tiktok_item_id: string;
  shopee_item_id: string;
  match_type: MatchType;
  confidence: number;
  status: MatchStatus;
  reasons: MatchReasons;
  rule_version?: string;
  model_version?: string;
  ingested_at?: string;
  batch_id?: string;
  schema_version?: string;
}

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
  reasons: AlertReasons;
  suggested_action?: string;
  batch_id?: string;
  schema_version?: string;
}

export interface DQResult {
  check_name: string;
  passed: boolean;
  actual_value: number;
  threshold: number;
  message: string;
}

export interface RunManifest {
  run_id: string;
  batch_id: string;
  schema_version: string;
  rule_version?: string;
  model_version?: string;
  created_at: string;
  parameters: Record<string, unknown>;
  row_counts: Record<string, number>;
  dq_results: DQResult[];
  dq_status: DQStatus;
  duration_seconds?: number;
}

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

export interface ReviewQueueItem {
  tiktok_item_id: string;
  shopee_item_id: string;
  tiktok_item: TopItem;
  shopee_item: TopItem;
  match_type: MatchType;
  confidence: number;
  reasons: MatchReasons;
  rule_version?: string;
}

export interface ReviewDecisionRequest {
  decision: "accept" | "reject" | "change_type";
  new_match_type?: MatchType;
  comment?: string;
}

export interface OurMappingRequest {
  our_status: OurStatus;
  our_sku_id?: string;
  notes?: string;
}

export interface PagedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface ErrorResponse {
  error: string;
  message: string;
  request_id?: string;
  timestamp?: string;
}
