import type { TopItemDetail, MatchResult } from "@/api/types";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatPrice, formatDate, formatPercent } from "@/utils/formatters";

interface ItemDetailDrawerProps {
  item: TopItemDetail | undefined;
  isLoading: boolean;
  isOpen: boolean;
  onClose: () => void;
}

function MatchCard({ match }: { match: MatchResult }) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusBadge variant={match.match_type} />
          <StatusBadge variant={match.status} />
        </div>
        <span className="text-sm font-semibold text-slate-700">
          {formatPercent(match.confidence)}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="font-medium text-slate-500">TikTok</p>
          <p className="text-slate-800">{match.tiktok_title ?? match.tiktok_item_id}</p>
        </div>
        <div>
          <p className="font-medium text-slate-500">Shopee</p>
          <p className="text-slate-800">{match.shopee_title ?? match.shopee_item_id}</p>
        </div>
      </div>
      {match.reasons && (
        <div className="mt-3 space-y-1">
          {match.reasons.strong_evidence.map((ev, i) => (
            <p key={i} className="text-xs text-emerald-600">
              + {ev}
            </p>
          ))}
          {match.reasons.weak_evidence.map((ev, i) => (
            <p key={i} className="text-xs text-amber-600">
              ~ {ev}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export function ItemDetailDrawer({
  item,
  isLoading,
  isOpen,
  onClose,
}: ItemDetailDrawerProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg overflow-y-auto bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-900">Item Detail</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 hover:bg-slate-100"
          >
            <svg
              className="h-5 w-5 text-slate-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="space-y-6 p-6">
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-20 animate-pulse rounded bg-slate-100" />
              ))}
            </div>
          ) : item ? (
            <>
              {/* Basic Info */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <StatusBadge variant={item.platform} />
                  <span className="text-sm text-slate-500">
                    Rank #{item.rank}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-slate-900">
                  {item.title}
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-500">Brand:</span>{" "}
                    <span className="font-medium text-slate-700">
                      {item.brand_std ?? item.brand_raw ?? "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Price:</span>{" "}
                    <span className="font-medium text-slate-700">
                      {formatPrice(
                        item.promo_price ?? item.list_price,
                        item.currency,
                      )}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Sold:</span>{" "}
                    <span className="font-medium text-slate-700">
                      {item.sold_range ?? "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Date:</span>{" "}
                    <span className="font-medium text-slate-700">
                      {formatDate(item.event_date)}
                    </span>
                  </div>
                </div>
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
                  >
                    View on {item.platform === "tiktok" ? "TikTok Shop" : "Shopee"} &rarr;
                  </a>
                )}
              </div>

              {/* Price History */}
              {item.price_history && item.price_history.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-semibold text-slate-700">
                    Price History
                  </h4>
                  <div className="overflow-hidden rounded-lg border border-slate-200">
                    <table className="min-w-full divide-y divide-slate-200">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-slate-500">
                            Date
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-slate-500">
                            List Price
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-slate-500">
                            Promo Price
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {item.price_history.map((ph) => (
                          <tr key={ph.event_date}>
                            <td className="px-3 py-2 text-sm text-slate-600">
                              {formatDate(ph.event_date)}
                            </td>
                            <td className="px-3 py-2 text-right text-sm text-slate-700">
                              {formatPrice(ph.list_price, item.currency)}
                            </td>
                            <td className="px-3 py-2 text-right text-sm text-slate-700">
                              {ph.promo_price != null
                                ? formatPrice(ph.promo_price, item.currency)
                                : "--"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Proxy History */}
              {item.proxy_history && item.proxy_history.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-semibold text-slate-700">
                    Sales Proxies
                  </h4>
                  <div className="overflow-hidden rounded-lg border border-slate-200">
                    <table className="min-w-full divide-y divide-slate-200">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-slate-500">
                            Date
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-slate-500">
                            Type
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-slate-500">
                            Value
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {item.proxy_history.map((ph, i) => (
                          <tr key={`${ph.event_date}-${ph.proxy_type}-${i}`}>
                            <td className="px-3 py-2 text-sm text-slate-600">
                              {formatDate(ph.event_date)}
                            </td>
                            <td className="px-3 py-2 text-sm text-slate-600">
                              {ph.proxy_type}
                            </td>
                            <td className="px-3 py-2 text-right text-sm text-slate-700">
                              {ph.proxy_value}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Matches */}
              {item.matches && item.matches.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-semibold text-slate-700">
                    Matches ({item.matches.length})
                  </h4>
                  <div className="space-y-3">
                    {item.matches.map((match, i) => (
                      <MatchCard key={i} match={match} />
                    ))}
                  </div>
                </div>
              )}

              {/* No matches */}
              {(!item.matches || item.matches.length === 0) && (
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center text-sm text-slate-500">
                  No cross-platform matches found for this item.
                </div>
              )}
            </>
          ) : (
            <div className="flex h-40 items-center justify-center text-sm text-slate-400">
              No item data available.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
