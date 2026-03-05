import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { getAlerts } from "@/api/endpoints";
import type { AlertsParams } from "@/api/types";

export function useAlerts(params: AlertsParams = {}) {
  return useQuery({
    queryKey: ["alerts", params],
    queryFn: () => getAlerts(params),
    placeholderData: keepPreviousData,
    staleTime: 2 * 60 * 1000,
  });
}
