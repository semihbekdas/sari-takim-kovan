import { NavLink, Outlet } from "react-router";

import { PageTree } from "../features/pages/PageTree";
import { BackendStatus } from "./BackendStatus";

/**
 * Ana yerleşim: solda menü (sayfa ağacı), sağda içerik. Her ekran `<Outlet />` içine çizilir.
 */
export function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Sol menü">
        <NavLink to="/" className="sidebar__brand">
          Kovan
        </NavLink>
        <PageTree />
        <BackendStatus />
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
