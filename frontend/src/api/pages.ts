import { apiRequest } from "./client";

/** Sol menüdeki bir sayfa (docs/api-contract.md "Sayfalar", `TreeNode`). */
export interface TreeNode {
  id: string;
  parent_id: string | null;
  title: string;
  has_children: boolean;
}

/** Breadcrumb'daki bir üst sayfa; en üstteki önce gelir (AC-05.2). */
export interface Breadcrumb {
  id: string;
  title: string;
}

/** `POST /pages` ve `GET /pages/{id}` yanıtı. İçerik (`content`) editörle birlikte Sprint 3'te kullanılacak. */
export interface Page {
  id: string;
  parent_id: string | null;
  title: string;
  version: number;
  index_status: "INDEXED" | "PENDING" | "FAILED";
  breadcrumbs: Breadcrumb[];
}

/** Sol menü: kullanıcının sayfaları, kardeşler başlığa göre Türkçe alfabetik (AC-05.1). */
export function getPageTree(signal?: AbortSignal): Promise<TreeNode[]> {
  return apiRequest<TreeNode[]>("/pages/tree", { signal });
}

/** Yeni sayfa; `parentId` verilirse alt sayfa olur. Başlık boşsa backend "Adsız" yapar (R-03). */
export function createPage(parentId: string | null): Promise<Page> {
  return apiRequest<Page>("/pages", { method: "POST", body: { parent_id: parentId } });
}
