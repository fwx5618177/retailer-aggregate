import type { TopItem } from "@/api/types";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatPrice, truncate } from "@/utils/formatters";

interface TopItemsTableProps {
  items: TopItem[];
  isLoading?: boolean;
  onRowClick: (item: TopItem) => void;
}

function SpecDisplay({ item }: { item: TopItem }) {
  const parts: string[] = [];
  if (item.size_value != null && item.size_unit) {
    parts.push(`${item.size_value}${item.size_unit}`);
  }
  if (item.pack_count != null && item.pack_count > 1) {
    parts.push(`x${item.pack_count}`);
  }
  return (
    <span className="text-slate-500">
      {parts.length > 0 ? parts.join(" ") : "--"}
    </span>
  );
}

export function TopItemsTable({
  items,
  isLoading = false,
  onRowClick,
}: TopItemsTableProps) {
  const columns: Column<TopItem>[] = [
    {
      key: "rank",
      header: "#",
      className: "w-12",
      sortable: true,
      render: (item) => (
        <span className="font-semibold text-slate-900">{item.rank}</span>
      ),
    },
    {
      key: "title",
      header: "Title",
      render: (item) => (
        <div className="max-w-sm">
          <p className="font-medium text-slate-800">
            {truncate(item.title, 55)}
          </p>
          {item.brand_std && (
            <p className="mt-0.5 text-xs text-slate-400">{item.brand_std}</p>
          )}
        </div>
      ),
    },
    {
      key: "brand",
      header: "Brand",
      render: (item) => (
        <span className="text-slate-700">
          {item.brand_std ?? item.brand_raw ?? "--"}
        </span>
      ),
    },
    {
      key: "spec",
      header: "Spec",
      render: (item) => <SpecDisplay item={item} />,
    },
    {
      key: "price",
      header: "Price",
      sortable: true,
      className: "text-right",
      render: (item) => (
        <div className="text-right">
          <span className="font-medium text-slate-800">
            {formatPrice(item.promo_price ?? item.list_price, item.currency)}
          </span>
          {item.promo_price != null &&
            item.list_price != null &&
            item.promo_price < item.list_price && (
              <p className="text-xs text-slate-400 line-through">
                {formatPrice(item.list_price, item.currency)}
              </p>
            )}
        </div>
      ),
    },
    {
      key: "platform",
      header: "Platform",
      className: "w-28",
      render: (item) => (
        <StatusBadge variant={item.platform} />
      ),
    },
    {
      key: "sold_range",
      header: "Sold",
      className: "w-24",
      render: (item) => (
        <span className="text-sm text-slate-500">
          {item.sold_range ?? "--"}
        </span>
      ),
    },
  ];

  return (
    <DataTable<TopItem>
      columns={columns}
      data={items}
      isLoading={isLoading}
      emptyMessage="No items found matching your filters."
      onRowClick={onRowClick}
      rowKey={(item) => `${item.platform}-${item.item_id}`}
    />
  );
}
