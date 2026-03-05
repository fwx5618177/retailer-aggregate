import type { MatchReasons } from "@/api/types";
import { formatPercent } from "@/utils/formatters";

interface ReasonsDisplayProps {
  reasons: MatchReasons;
}

export function ReasonsDisplay({ reasons }: ReasonsDisplayProps) {
  return (
    <div className="space-y-3">
      {/* Strong Evidence */}
      {reasons.strong_evidence.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-emerald-700">
            Strong Evidence
          </p>
          <ul className="space-y-1">
            {reasons.strong_evidence.map((ev, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-emerald-600"
              >
                <svg
                  className="mt-0.5 h-4 w-4 shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                {ev}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weak Evidence */}
      {reasons.weak_evidence.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-amber-700">
            Weak Evidence
          </p>
          <ul className="space-y-1">
            {reasons.weak_evidence.map((ev, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-amber-600"
              >
                <svg
                  className="mt-0.5 h-4 w-4 shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
                  />
                </svg>
                {ev}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Field Alignment Table */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-600">
          Field Alignment
        </p>
        <div className="overflow-hidden rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-500">
                  Field
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-500">
                  TikTok
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-500">
                  Shopee
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-slate-500">
                  Match
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="px-3 py-2 font-medium text-slate-700">Brand</td>
                <td className="px-3 py-2 text-slate-600">
                  {reasons.field_alignment.brand_a ?? "N/A"}
                </td>
                <td className="px-3 py-2 text-slate-600">
                  {reasons.field_alignment.brand_b ?? "N/A"}
                </td>
                <td className="px-3 py-2 text-center">
                  {reasons.field_alignment.brand_match ? (
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                  ) : (
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-rose-100 text-rose-600">
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </span>
                  )}
                </td>
              </tr>
              <tr>
                <td className="px-3 py-2 font-medium text-slate-700">Spec</td>
                <td className="px-3 py-2 text-slate-600">
                  {reasons.field_alignment.spec_a ?? "N/A"}
                </td>
                <td className="px-3 py-2 text-slate-600">
                  {reasons.field_alignment.spec_b ?? "N/A"}
                </td>
                <td className="px-3 py-2 text-center">
                  {reasons.field_alignment.spec_match ? (
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                  ) : (
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-rose-100 text-rose-600">
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </span>
                  )}
                </td>
              </tr>
              <tr>
                <td className="px-3 py-2 font-medium text-slate-700">
                  Price Band
                </td>
                <td className="px-3 py-2 text-slate-600" colSpan={2}>
                  --
                </td>
                <td className="px-3 py-2 text-center">
                  {reasons.field_alignment.price_band_match ? (
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                  ) : (
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-rose-100 text-rose-600">
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </span>
                  )}
                </td>
              </tr>
              <tr>
                <td className="px-3 py-2 font-medium text-slate-700">
                  Title Similarity
                </td>
                <td className="px-3 py-2 text-slate-600" colSpan={2}>
                  {formatPercent(reasons.field_alignment.title_similarity)}
                </td>
                <td className="px-3 py-2 text-center">
                  <span className="text-xs font-medium text-slate-600">
                    {formatPercent(reasons.field_alignment.title_similarity)}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Missing Fields */}
      {reasons.missing_fields.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Missing Fields
          </p>
          <div className="flex flex-wrap gap-1.5">
            {reasons.missing_fields.map((field, i) => (
              <span
                key={i}
                className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-500"
              >
                {field}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
