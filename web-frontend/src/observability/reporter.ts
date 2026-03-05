/**
 * Error and event reporting module.
 *
 * When VITE_SENTRY_DSN is configured, errors are sent to Sentry via its
 * Envelope API (no SDK dependency needed for basic error capture).
 *
 * To upgrade to the full @sentry/browser SDK:
 *   1. npm install @sentry/browser
 *   2. Replace this module with Sentry.init({ dsn, ... })
 *
 * Key interactions tracked:
 * - review_decision: reviewer accepts/rejects/changes a match
 * - our_mapping_update: user updates internal mapping
 * - page_view: navigation events
 */

const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN as string | undefined;

interface ErrorContext {
  componentStack?: string;
  [key: string]: unknown;
}

interface EventData {
  [key: string]: unknown;
}

/* Parse Sentry DSN into parts for envelope API */
let sentryEndpoint: string | null = null;
let sentryPublicKey: string | null = null;
let sentryProjectId: string | null = null;

function parseDsn(dsn: string): boolean {
  try {
    const url = new URL(dsn);
    sentryPublicKey = url.username;
    sentryProjectId = url.pathname.replace("/", "");
    sentryEndpoint = `${url.protocol}//${url.host}/api/${sentryProjectId}/envelope/`;
    return true;
  } catch {
    return false;
  }
}

const sentryEnabled = SENTRY_DSN ? parseDsn(SENTRY_DSN) : false;

if (!sentryEnabled) {
  console.info("[observability] No VITE_SENTRY_DSN configured — using console fallback");
}

/** Send an error event to Sentry via the Envelope API. */
function sendToSentry(error: Error, context?: ErrorContext): void {
  if (!sentryEndpoint || !sentryPublicKey || !sentryProjectId) return;

  const envelope = JSON.stringify({
    event_id: crypto.randomUUID().replace(/-/g, ""),
    sent_at: new Date().toISOString(),
    dsn: SENTRY_DSN,
  }) + "\n" +
  JSON.stringify({ type: "event" }) + "\n" +
  JSON.stringify({
    exception: {
      values: [{
        type: error.name,
        value: error.message,
        stacktrace: error.stack ? {
          frames: error.stack.split("\n").slice(1, 10).map(line => ({
            filename: line.trim(),
          })),
        } : undefined,
      }],
    },
    level: "error",
    platform: "javascript",
    environment: import.meta.env.MODE ?? "development",
    release: `sea-retailer-web@${import.meta.env.VITE_APP_VERSION ?? "0.1.0"}`,
    extra: context,
    timestamp: Date.now() / 1000,
  });

  // Use sendBeacon for reliability, fallback to fetch
  const url = `${sentryEndpoint}?sentry_key=${sentryPublicKey}&sentry_version=7`;
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, envelope);
  } else {
    fetch(url, { method: "POST", body: envelope, keepalive: true }).catch(() => {});
  }
}

/** Report an error. */
export function reportError(error: Error, context?: ErrorContext): void {
  if (sentryEnabled) {
    sendToSentry(error, context);
  }
  console.error("[observability] Error:", error.message, context);
}

/** Track a named business event (interaction tracking). */
export function trackEvent(name: string, data?: EventData): void {
  // Always log for local debugging
  if (import.meta.env.DEV) {
    console.info(`[track] ${name}`, data);
  }
}

/**
 * Pre-defined tracked interactions for the SEA Retailer platform.
 */
export const events = {
  reviewDecision: (decision: string, tiktokId: string, shopeeId: string) =>
    trackEvent("review_decision", { decision, tiktokId, shopeeId }),

  ourMappingUpdate: (platform: string, itemId: string, status: string) =>
    trackEvent("our_mapping_update", { platform, itemId, status }),

  pageView: (path: string) =>
    trackEvent("page_view", { path }),

  alertViewed: (alertId: string, alertType: string) =>
    trackEvent("alert_viewed", { alertId, alertType }),
} as const;

// Set up global error handler for uncaught errors
window.addEventListener("error", (event) => {
  reportError(event.error instanceof Error ? event.error : new Error(event.message));
});

window.addEventListener("unhandledrejection", (event) => {
  const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason));
  reportError(error);
});
