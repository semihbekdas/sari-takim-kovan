import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, useNavigate } from "react-router";

import { ApiError } from "../../api/client";
import { createPage, getPageTree, type TreeNode } from "../../api/pages";
import { groupByParent, PAGE_TREE_KEY } from "./groupPages";

/** Sol menüdeki sayfa ağacı ve "Yeni sayfa" düğmesi (US-03, US-05). */
export function PageTree() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const tree = useQuery({
    queryKey: PAGE_TREE_KEY,
    queryFn: ({ signal }) => getPageTree(signal),
  });
  const create = useMutation({
    mutationFn: createPage,
    onSuccess: async (page) => {
      // Yeni sayfa menüde hemen görünsün (AC-03.1) ve açılsın.
      await queryClient.invalidateQueries({ queryKey: PAGE_TREE_KEY });
      await navigate(`/pages/${page.id}`);
    },
  });

  return (
    <nav className="sidebar__nav" aria-label="Sayfalar">
      <button
        type="button"
        className="page-tree__new"
        disabled={create.isPending}
        onClick={() => create.mutate(null)}
      >
        + Yeni sayfa
      </button>
      {create.isError && <p className="page-tree__message">Sayfa oluşturulamadı.</p>}
      <TreeBody
        isPending={tree.isPending}
        error={tree.error}
        nodes={tree.data}
        onAddChild={(parentId) => create.mutate(parentId)}
      />
    </nav>
  );
}

interface TreeBodyProps {
  isPending: boolean;
  error: Error | null;
  nodes: TreeNode[] | undefined;
  onAddChild: (parentId: string) => void;
}

function TreeBody({ isPending, error, nodes, onAddChild }: Readonly<TreeBodyProps>) {
  if (isPending) {
    return <p className="page-tree__message">Sayfalar yükleniyor…</p>;
  }
  if (error !== null) {
    const unauthorized = error instanceof ApiError && error.status === 401;
    return (
      <p className="page-tree__message">
        {unauthorized ? "Sayfalarını görmek için giriş yap." : "Sayfalar yüklenemedi."}
      </p>
    );
  }
  if (nodes === undefined || nodes.length === 0) {
    return <p className="page-tree__message">Henüz sayfa yok.</p>;
  }
  return <TreeLevel parentId={null} groups={groupByParent(nodes)} onAddChild={onAddChild} />;
}

interface TreeLevelProps {
  parentId: string | null;
  groups: Map<string | null, TreeNode[]>;
  onAddChild: (parentId: string) => void;
}

/** Bir sayfanın alt sayfaları; her alt sayfa kendi alt sayfalarını yine bu bileşenle çizer. */
function TreeLevel({ parentId, groups, onAddChild }: Readonly<TreeLevelProps>) {
  const nodes = groups.get(parentId) ?? [];
  return (
    <ul className="page-tree">
      {nodes.map((node) => (
        <li key={node.id}>
          <div className="page-tree__row">
            <NavLink to={`/pages/${node.id}`} className="page-tree__link">
              {node.title}
            </NavLink>
            <button
              type="button"
              className="page-tree__add"
              aria-label={`${node.title} altına sayfa ekle`}
              onClick={() => onAddChild(node.id)}
            >
              +
            </button>
          </div>
          {node.has_children && (
            <TreeLevel parentId={node.id} groups={groups} onAddChild={onAddChild} />
          )}
        </li>
      ))}
    </ul>
  );
}
