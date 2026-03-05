import { useQuery } from "@tanstack/react-query";
import { getItemDetail } from "@/api/endpoints";

export function useItemDetail(platform: string, itemId: string) {
  return useQuery({
    queryKey: ["itemDetail", platform, itemId],
    queryFn: () => getItemDetail(platform, itemId),
    enabled: !!platform && !!itemId,
    staleTime: 5 * 60 * 1000,
  });
}
