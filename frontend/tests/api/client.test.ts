import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiRequest, NETWORK_ERROR, UNKNOWN_ERROR } from "../../src/api/client";

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function mockFetch(response: Response | Error) {
  const fetchMock = vi.fn<typeof fetch>();
  if (response instanceof Error) {
    fetchMock.mockRejectedValue(response);
  } else {
    fetchMock.mockResolvedValue(response);
  }
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function catchApiError(promise: Promise<unknown>): Promise<ApiError> {
  const error = await promise.catch((caught: unknown) => caught);
  expect(error).toBeInstanceOf(ApiError);
  return error as ApiError;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("returns the JSON body of a successful response", async () => {
    mockFetch(jsonResponse(200, { status: "ok" }));

    await expect(apiRequest("/health")).resolves.toEqual({ status: "ok" });
  });

  it("calls /api/v1 with the session cookie and a JSON body", async () => {
    const fetchMock = mockFetch(jsonResponse(201, { id: "1" }));

    await apiRequest("/pages", { method: "POST", body: { title: "Notlar" } });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/pages",
      expect.objectContaining({
        method: "POST",
        credentials: "same-origin",
        body: JSON.stringify({ title: "Notlar" }),
        headers: expect.objectContaining({ "Content-Type": "application/json" }) as unknown,
      }),
    );
  });

  it("returns undefined for 204 No Content", async () => {
    mockFetch(new Response(null, { status: 204 }));

    await expect(apiRequest("/auth/logout", { method: "POST" })).resolves.toBeUndefined();
  });

  it("turns the API error format into an ApiError", async () => {
    mockFetch(
      jsonResponse(422, {
        error: {
          code: "PAGE_MOVE_CYCLE",
          message: "Bir sayfa kendi alt sayfasının altına taşınamaz.",
          rule: "R-05",
          request_id: "8f2c1a7e",
        },
      }),
    );

    const error = await catchApiError(apiRequest("/pages/1/move", { method: "PATCH", body: {} }));

    expect(error.status).toBe(422);
    expect(error.code).toBe("PAGE_MOVE_CYCLE");
    expect(error.message).toBe("Bir sayfa kendi alt sayfasının altına taşınamaz.");
    expect(error.rule).toBe("R-05");
    expect(error.requestId).toBe("8f2c1a7e");
    expect(error.details).toEqual([]);
  });

  it("keeps field details of a validation error", async () => {
    const details = [{ field: "body.email", message: "Bu alan zorunludur." }];
    mockFetch(
      jsonResponse(422, {
        error: {
          code: "VALIDATION_ERROR",
          message: "Geçersiz istek.",
          rule: null,
          request_id: "r1",
          details,
        },
      }),
    );

    const error = await catchApiError(apiRequest("/auth/register", { method: "POST", body: {} }));

    expect(error.code).toBe("VALIDATION_ERROR");
    expect(error.rule).toBeNull();
    expect(error.details).toEqual(details);
  });

  it("uses UNKNOWN_ERROR when the error body is not in the API format", async () => {
    mockFetch(
      new Response("<html>Bad Gateway</html>", {
        status: 502,
        headers: { "X-Request-ID": "r2" },
      }),
    );

    const error = await catchApiError(apiRequest("/health"));

    expect(error.status).toBe(502);
    expect(error.code).toBe(UNKNOWN_ERROR);
    expect(error.requestId).toBe("r2");
  });

  it("uses NETWORK_ERROR when the server cannot be reached", async () => {
    mockFetch(new TypeError("Failed to fetch"));

    const error = await catchApiError(apiRequest("/health"));

    expect(error.status).toBe(0);
    expect(error.code).toBe(NETWORK_ERROR);
  });
});
