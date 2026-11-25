import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "./api/client";

/** 4xx hataları (yetkisiz, bulunamadı, geçersiz) tekrar denemekle düzelmez. */
function shouldRetry(failureCount: number, error: Error): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: shouldRetry, refetchOnWindowFocus: false },
    },
  });
}
