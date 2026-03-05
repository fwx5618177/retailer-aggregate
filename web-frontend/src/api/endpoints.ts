import apiClient from "./client";
import type {
  OverviewResponse,
  OverviewParams,
  TopItem,
  TopItemDetail,
  TopItemsParams,
  Alert,
  AlertsParams,
  ReviewQueueItem,
  ReviewQueueParams,
  ReviewDecisionRequest,
  ReviewDecisionResponse,
  OurMapping,
  OurMappingRequest,
  PagedResponse,
} from "./types";

/* ─── Overview ─── */

export async function getOverview(
  params: OverviewParams = {},
): Promise<OverviewResponse> {
  const { data } = await apiClient.get<OverviewResponse>("/overview", {
    params,
  });
  return data;
}

/* ─── Top Items ─── */

export async function getTopItems(
  params: TopItemsParams = {},
): Promise<PagedResponse<TopItem>> {
  const { data } = await apiClient.get<PagedResponse<TopItem>>("/top-items", {
    params,
  });
  return data;
}

export async function getItemDetail(
  platform: string,
  itemId: string,
): Promise<TopItemDetail> {
  const { data } = await apiClient.get<TopItemDetail>(
    `/items/${platform}/${itemId}`,
  );
  return data;
}

/* ─── Alerts ─── */

export async function getAlerts(
  params: AlertsParams = {},
): Promise<PagedResponse<Alert>> {
  const { data } = await apiClient.get<PagedResponse<Alert>>("/alerts", {
    params,
  });
  return data;
}

/* ─── Review Queue ─── */

export async function getReviewQueue(
  params: ReviewQueueParams = {},
): Promise<PagedResponse<ReviewQueueItem>> {
  const { data } = await apiClient.get<PagedResponse<ReviewQueueItem>>(
    "/review-queue",
    { params },
  );
  return data;
}

export async function submitReviewDecision(
  tiktokItemId: string,
  shopeeItemId: string,
  request: ReviewDecisionRequest,
): Promise<ReviewDecisionResponse> {
  const { data } = await apiClient.post<ReviewDecisionResponse>(
    `/review/${tiktokItemId}/${shopeeItemId}/decision`,
    request,
    {
      headers: {
        "Idempotency-Key": crypto.randomUUID(),
      },
    },
  );
  return data;
}

/* ─── Our Mapping ─── */

export async function getOurMapping(
  platform: string,
  itemId: string,
): Promise<OurMapping> {
  const { data } = await apiClient.get<OurMapping>(
    `/our-mapping/${platform}/${itemId}`,
  );
  return data;
}

export async function updateOurMapping(
  platform: string,
  itemId: string,
  request: OurMappingRequest,
): Promise<{ status: string; message: string }> {
  const { data } = await apiClient.post<{ status: string; message: string }>(
    `/our-mapping/${platform}/${itemId}`,
    request,
  );
  return data;
}
