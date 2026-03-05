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

interface OverlapChartProps {
  overlap?: {
    exact_same: number;
    variant_family: number;
    similar: number;
    total_matched: number;
  };
  isLoading?: boolean;
}

export function OverlapChart({ overlap, isLoading = false }: OverlapChartProps) {
  if (isLoading) {
    return (
      <div className="card">
        <h3 className="mb-4 text-base font-semibold text-slate-800">
          Match Overlap
        </h3>
        <div className="flex h-64 items-center justify-center">
          <div className="h-48 w-full animate-pulse rounded bg-slate-100" />
        </div>
      </div>
    );
  }

  const data = [
    {
      name: "Exact Same",
      count: overlap?.exact_same ?? 0,
      fill: "#10b981",
    },
    {
      name: "Variant Family",
      count: overlap?.variant_family ?? 0,
      fill: "#0ea5e9",
    },
    {
      name: "Similar",
      count: overlap?.similar ?? 0,
      fill: "#8b5cf6",
    },
  ];

  return (
    <div className="card">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-800">
          Match Overlap
        </h3>
        <span className="text-sm text-slate-500">
          Total matched: {overlap?.total_matched ?? 0}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis type="number" tick={{ fontSize: 12, fill: "#64748b" }} />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            tick={{ fontSize: 12, fill: "#64748b" }}
          />
          <Tooltip
            contentStyle={{
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            }}
          />
          <Legend />
          <Bar dataKey="count" name="Items" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
