import { describe, expect, it } from "vitest";

import type { TreeNode } from "../../src/api/pages";
import { groupByParent } from "../../src/features/pages/groupPages";

function node(id: string, parentId: string | null, title: string): TreeNode {
  return { id, parent_id: parentId, title, has_children: false };
}

describe("groupByParent", () => {
  it("groups pages under their parent and keeps the backend's alphabetical order", () => {
    const nodes = [node("1", null, "Çay"), node("2", "1", "İz"), node("3", "1", "Işık")];

    const groups = groupByParent(nodes);

    expect(groups.get(null)?.map((n) => n.title)).toEqual(["Çay"]);
    expect(groups.get("1")?.map((n) => n.title)).toEqual(["İz", "Işık"]);
  });

  it("puts a page whose parent is missing from the list at the top instead of losing it", () => {
    const groups = groupByParent([node("2", "kesilen-ust-sayfa", "Yetim")]);

    expect(groups.get(null)?.map((n) => n.title)).toEqual(["Yetim"]);
  });
});
