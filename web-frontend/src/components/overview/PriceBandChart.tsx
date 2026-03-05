import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface PriceBandChartProps {
  data?: Array<{
    band: string;
    tiktok_count: number;
    shopee_count: number;
  }>;
  isLoading?: boolean;
}

export function PriceBandChart({
  data,
  isLoading = false,
}: PriceBandChartProps) {
  if (isLoading) {
    return (
      <div className="card">
        <h3 className="mb-4 text-base font-semibold text-slate-800">
          Price Band Distribution
        </h3>
        <div className="flex h-64 items-center justify-center">
          <div className="h-48 w-full animate-pulse rounded bg-slate-100" />
        </div>
      </div>
    );
  }

  const chartData = data ?? [];

  return (
    <div className="card">
      <h3 className="mb-4 text-base font-semibold text-slate-800">
        Price Band Distribution
      </h3>
      {chartData.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-slate-400">
          No price band data available.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="band"
              tick={{ fontSize: 11, fill: "#64748b" }}
              angle={-30}
              textAnchor="end"
              height={60}
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
            <Bar
              dataKey="tiktok_count"
              name="TikTok"
              fill="#1e1e1e"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="shopee_count"
              name="Shopee"
              fill="#ee4d2d"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
