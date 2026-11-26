import type { RouteObject } from "react-router";

import { Layout } from "./components/Layout";
import { HomePage } from "./features/pages/HomePage";
import { NotFoundPage } from "./features/pages/NotFoundPage";

/** Uygulamanın adresleri. Yeni ekranlar (giriş, sayfa, sohbet …) buraya eklenir. */
export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
