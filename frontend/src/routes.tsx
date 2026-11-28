import type { RouteObject } from "react-router";

import { Layout } from "./components/Layout";
import { HomePage } from "./features/pages/HomePage";
import { NotFoundPage } from "./features/pages/NotFoundPage";
import { PageView } from "./features/pages/PageView";

/** Uygulamanın adresleri. Yeni ekranlar (giriş, sayfa, sohbet …) buraya eklenir. */
export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "pages/:pageId", element: <PageView /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
