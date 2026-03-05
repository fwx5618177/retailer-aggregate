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
