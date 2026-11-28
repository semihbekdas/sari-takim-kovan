import type { TreeNode } from "../../api/pages";

/** Sayfa ağacının TanStack Query anahtarı; sayfa eklenince bu anahtar yenilenir. */
export const PAGE_TREE_KEY = ["pages", "tree"] as const;

/**
 * Düz listeyi üst sayfaya göre gruplar: `children.get(null)` en üst düzeydeki sayfalardır.
 * Backend kardeşleri zaten Türkçe alfabetik sıraladığı için sıra korunur, yeniden sıralanmaz.
 * Üst sayfası listede olmayan (ör. 1000 sınırında kesilmiş) sayfa en üste konur, kaybolmaz.
 */
export function groupByParent(nodes: TreeNode[]): Map<string | null, TreeNode[]> {
  const ids = new Set(nodes.map((node) => node.id));
  const children = new Map<string | null, TreeNode[]>();
  for (const node of nodes) {
    const parent = node.parent_id !== null && ids.has(node.parent_id) ? node.parent_id : null;
    const siblings = children.get(parent) ?? [];
    siblings.push(node);
    children.set(parent, siblings);
  }
  return children;
}
