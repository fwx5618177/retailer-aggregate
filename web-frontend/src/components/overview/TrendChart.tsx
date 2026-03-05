import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

/**
 * Placeholder for trend data.
 * Once the API supports multi-date overview trends, wire this up.
 * For now it renders a mock dataset to show the chart pattern.
 */

const MOCK_TREND_DATA = [
  { date: "Feb 01", tiktok: 42, shopee: 38, matched: 28 },
  { date: "Feb 03", tiktok: 44, shopee: 40, matched: 30 },
  { date: "Feb 05", tiktok: 45, shopee: 41, matched: 31 },
  { date: "Feb 07", tiktok: 48, shopee: 43, matched: 33 },
  { date: "Feb 09", tiktok: 47, shopee: 44, matched: 35 },
  { date: "Feb 11", tiktok: 50, shopee: 46, matched: 37 },
  { date: "Feb 13", tiktok: 50, shopee: 48, matched: 39 },
  { date: "Feb 15", tiktok: 50, shopee: 50, matched: 40 },
];

interface TrendChartProps {
  isLoading?: boolean;
}

export function TrendChart({ isLoading = false }: TrendChartProps) {
  if (isLoading) {
    return (
      <div className="card">
        <h3 className="mb-4 text-base font-semibold text-slate-800">
          Trend (14d)
        </h3>
        <div className="flex h-64 items-center justify-center">
          <div className="h-48 w-full animate-pulse rounded bg-slate-100" />
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-800">
          Trend (14d)
        </h3>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
          Preview
        </span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={MOCK_TREND_DATA}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: "#64748b" }}
          />
          <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
          <Tooltip
            contentStyle={{
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="tiktok"
            name="TikTok"
            stroke="#1e1e1e"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="shopee"
            name="Shopee"
            stroke="#ee4d2d"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="matched"
            name="Matched"
            stroke="#6366f1"
            strokeWidth={2}
            dot={{ r: 3 }}
            strokeDasharray="4 4"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
