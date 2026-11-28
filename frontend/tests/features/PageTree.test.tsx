import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../src/api/client";
import { getHealth } from "../../src/api/health";
import { createPage, getPage, getPageTree, type Page } from "../../src/api/pages";
import { renderApp } from "./renderApp";

vi.mock("../../src/api/health");
vi.mock("../../src/api/pages");

const DERSLER = { id: "d", parent_id: null, title: "Dersler", has_children: true };
const VERITABANI = { id: "v", parent_id: "d", title: "Veritabanı", has_children: false };
const ZIL = { id: "z", parent_id: null, title: "Zil", has_children: false };

function page(id: string, title: string): Page {
  return { id, parent_id: null, title, version: 1, index_status: "PENDING", breadcrumbs: [] };
}

afterEach(() => {
  vi.resetAllMocks();
});

describe("PageTree", () => {
  it("shows a child page under its parent (AC-05.1)", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getPageTree).mockResolvedValue([DERSLER, VERITABANI, ZIL]);

    renderApp("/");

    const menu = screen.getByRole("navigation", { name: "Sayfalar" });
    const dersler = (await within(menu).findByRole("link", { name: "Dersler" })).closest("li");
    expect(dersler).not.toBeNull();
    expect(
      within(dersler as HTMLElement).getByRole("link", { name: "Veritabanı" }),
    ).toHaveAttribute("href", "/pages/v");
    const order = within(menu)
      .getAllByRole("link")
      .map((link) => link.textContent);
    expect(order).toEqual(["Dersler", "Veritabanı", "Zil"]);
  });

  it("creates a page, refreshes the menu and opens the new page (AC-03.1)", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getPageTree)
      .mockResolvedValueOnce([])
      .mockResolvedValue([{ id: "yeni", parent_id: null, title: "Adsız", has_children: false }]);
    vi.mocked(createPage).mockResolvedValue(page("yeni", "Adsız"));
    vi.mocked(getPage).mockResolvedValue(page("yeni", "Adsız"));
    const router = renderApp("/");

    await userEvent.click(await screen.findByRole("button", { name: "+ Yeni sayfa" }));

    expect(createPage).toHaveBeenCalledWith(null, expect.anything());
    expect(await screen.findByRole("link", { name: "Adsız" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/pages/yeni");
  });

  it("adds a sub-page under the chosen page (US-05)", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getPageTree).mockResolvedValue([ZIL]);
    vi.mocked(createPage).mockResolvedValue(page("alt", "Adsız"));
    vi.mocked(getPage).mockResolvedValue(page("alt", "Adsız"));
    renderApp("/");

    await userEvent.click(await screen.findByRole("button", { name: "Zil altına sayfa ekle" }));

    expect(createPage).toHaveBeenCalledWith("z", expect.anything());
  });

  it("asks the user to log in when the session is missing", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getPageTree).mockRejectedValue(new ApiError(401, "UNAUTHORIZED", "Oturum yok."));

    renderApp("/");

    expect(await screen.findByText("Sayfalarını görmek için giriş yap.")).toBeInTheDocument();
  });
});
