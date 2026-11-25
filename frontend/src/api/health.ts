import { apiRequest } from "./client";

/** GET /api/v1/health: Backend ayakta mı? (docs/api-contract.md "Sağlık") */
export interface HealthResponse {
  status: "ok";
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health", { signal });
}
