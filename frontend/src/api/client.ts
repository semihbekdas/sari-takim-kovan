/**
 * Tipli API istemcisi: Frontend'deki tüm backend istekleri buradan geçer.
 * Bileşenler doğrudan `fetch` çağırmaz (ADR-007).
 */

export const API_BASE = "/api/v1";

/** `VALIDATION_ERROR` yanıtındaki alan hatası (docs/api-contract.md "Hata formatı"). */
export interface ApiErrorDetail {
  field: string;
  message: string;
}

/** Backend'in hata gövdesi (docs/api-contract.md "Hata formatı"). */
interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    rule: string | null;
    request_id: string | null;
    details?: ApiErrorDetail[];
  };
}

/** Başarısız her istek bu tek hata tipine dönüşür; ekranlar `code`'a göre karar verir. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly rule: string | null;
  readonly requestId: string | null;
  readonly details: ApiErrorDetail[];

  constructor(
    status: number,
    code: string,
    message: string,
    options: { rule?: string | null; requestId?: string | null; details?: ApiErrorDetail[] } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.rule = options.rule ?? null;
    this.requestId = options.requestId ?? null;
    this.details = options.details ?? [];
  }
}

/** Sunucuya hiç ulaşılamadığında (ağ yok, backend kapalı) kullanılan kod. */
export const NETWORK_ERROR = "NETWORK_ERROR";
/** Hata gövdesi beklenen biçimde değilse (ör. proxy'nin HTML hata sayfası) kullanılan kod. */
export const UNKNOWN_ERROR = "UNKNOWN_ERROR";

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

/**
 * `/api/v1` altındaki bir uç noktayı çağırır. Başarılıysa JSON gövdeyi `T` olarak döndürür
 * (204'te `undefined`), başarısızsa `ApiError` fırlatır.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = options;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "include", // oturum çerezi (`kovan_session`) her istekte gider
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error; // iptal edilen istek hata sayılmaz; TanStack Query bunu kendisi yönetir
    }
    throw new ApiError(0, NETWORK_ERROR, "Sunucuya ulaşılamadı.");
  }

  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function toApiError(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null);
  if (isApiErrorBody(body)) {
    const { code, message, rule, request_id, details } = body.error;
    return new ApiError(response.status, code, message, {
      rule,
      requestId: request_id,
      details,
    });
  }
  return new ApiError(response.status, UNKNOWN_ERROR, "Beklenmeyen bir hata oluştu.", {
    requestId: response.headers.get("X-Request-ID"),
  });
}

function isApiErrorBody(body: unknown): body is ApiErrorBody {
  if (typeof body !== "object" || body === null || !("error" in body)) {
    return false;
  }
  const error: unknown = body.error;
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string"
  );
}
