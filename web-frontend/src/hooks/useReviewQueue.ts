import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { getReviewQueue, submitReviewDecision } from "@/api/endpoints";
import type { ReviewQueueParams, ReviewDecisionRequest } from "@/api/types";

export function useReviewQueue(params: ReviewQueueParams = {}) {
  return useQuery({
    queryKey: ["reviewQueue", params],
    queryFn: () => getReviewQueue(params),
    placeholderData: keepPreviousData,
    staleTime: 60 * 1000,
  });
}

export function useSubmitDecision() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tiktokItemId,
      shopeeItemId,
      request,
    }: {
      tiktokItemId: string;
      shopeeItemId: string;
      request: ReviewDecisionRequest;
    }) => submitReviewDecision(tiktokItemId, shopeeItemId, request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["reviewQueue"] });
      void queryClient.invalidateQueries({ queryKey: ["overview"] });
    },
  });
}
