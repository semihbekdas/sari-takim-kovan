import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../src/api/client";
import { getHealth } from "../../src/api/health";
import { getPage, getPageTree } from "../../src/api/pages";
import { renderApp } from "./renderApp";

vi.mock("../../src/api/health");
vi.mock("../../src/api/pages");

afterEach(() => {
  vi.resetAllMocks();
});

describe("PageView", () => {
  it("shows the breadcrumb above the open page (AC-05.2)", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getPageTree).mockResolvedValue([]);
    vi.mocked(getPage).mockResolvedValue({
      id: "n",
      parent_id: "v",
      title: "Normalizasyon",
      version: 3,
      index_status: "INDEXED",
      breadcrumbs: [
        { id: "d", title: "Dersler" },
        { id: "v", title: "Veritabanı" },
      ],
    });

    renderApp("/pages/n");

    const breadcrumb = await screen.findByRole("navigation", { name: "Konum" });
    expect(breadcrumb).toHaveTextContent("DerslerVeritabanıNormalizasyon");
    expect(screen.getByRole("link", { name: "Dersler" })).toHaveAttribute("href", "/pages/d");
    expect(screen.getByRole("heading", { name: "Normalizasyon" })).toBeInTheDocument();
    expect(getPage).toHaveBeenCalledWith("n", expect.anything());
  });

  it("says the page was not found for another user's or a missing page (R-04)", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getPageTree).mockResolvedValue([]);
    vi.mocked(getPage).mockRejectedValue(new ApiError(404, "PAGE_NOT_FOUND", "Sayfa bulunamadı."));

    renderApp("/pages/baskasinin");

    expect(await screen.findByText("Bu sayfa bulunamadı.")).toBeInTheDocument();
  });
});
