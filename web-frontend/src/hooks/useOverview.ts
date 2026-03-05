import { useQuery } from "@tanstack/react-query";
import { getOverview } from "@/api/endpoints";
import type { OverviewParams } from "@/api/types";

export function useOverview(params: OverviewParams = {}) {
  return useQuery({
    queryKey: ["overview", params],
    queryFn: () => getOverview(params),
    staleTime: 5 * 60 * 1000,
  });
}
