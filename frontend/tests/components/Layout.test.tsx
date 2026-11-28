import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, NETWORK_ERROR } from "../../src/api/client";
import { getHealth } from "../../src/api/health";
import { getPageTree } from "../../src/api/pages";
import { routes } from "../../src/routes";

vi.mock("../../src/api/health");
vi.mock("../../src/api/pages");

function renderAt(path: string) {
  vi.mocked(getPageTree).mockResolvedValue([]);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.resetAllMocks();
});

describe("Layout", () => {
  it("shows the left menu and the home page in the content area", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });

    renderAt("/");

    expect(screen.getByRole("complementary", { name: "Sol menü" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent("Kovan'a hoş geldin");
    expect(await screen.findByText("Sunucu: bağlı")).toBeInTheDocument();
  });

  it("tells the user when the backend cannot be reached", async () => {
    vi.mocked(getHealth).mockRejectedValue(new ApiError(0, NETWORK_ERROR, "Sunucuya ulaşılamadı."));

    renderAt("/");

    expect(await screen.findByText("Sunucu: bağlanılamadı")).toBeInTheDocument();
  });

  it("shows a not-found page for unknown addresses, inside the layout", () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });

    renderAt("/olmayan-adres");

    expect(screen.getByRole("heading", { name: "Sayfa bulunamadı" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Sol menü" })).toBeInTheDocument();
  });
});
