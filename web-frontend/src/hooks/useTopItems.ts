import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { getTopItems } from "@/api/endpoints";
import type { TopItemsParams } from "@/api/types";

export function useTopItems(params: TopItemsParams = {}) {
  return useQuery({
    queryKey: ["topItems", params],
    queryFn: () => getTopItems(params),
    placeholderData: keepPreviousData,
    staleTime: 2 * 60 * 1000,
  });
}
