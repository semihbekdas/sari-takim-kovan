import { NavLink, Outlet } from "react-router";

import { BackendStatus } from "./BackendStatus";

/**
 * Ana yerleşim: solda menü, sağda içerik. Her sayfa `<Outlet />` içine çizilir.
 * Sayfa ağacı ve breadcrumb #10'da sol menüye eklenecek.
 */
export function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Sol menü">
        <NavLink to="/" className="sidebar__brand">
          Kovan
        </NavLink>
        <nav className="sidebar__nav" aria-label="Sayfalar">
          <p className="sidebar__empty">Henüz sayfa yok.</p>
        </nav>
        <BackendStatus />
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
