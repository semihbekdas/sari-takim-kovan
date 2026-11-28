import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";

import { ApiError } from "../../api/client";
import { getPage, type Page } from "../../api/pages";

/** Açık sayfa: üstte breadcrumb, altında başlık (US-03, AC-05.2). Editör Sprint 3'te gelecek. */
export function PageView() {
  const { pageId = "" } = useParams();
  const page = useQuery({
    queryKey: ["pages", pageId],
    queryFn: ({ signal }) => getPage(pageId, signal),
  });

  if (page.isPending) {
    return <p>Sayfa yükleniyor…</p>;
  }
  if (page.isError) {
    // Başkasının sayfası da 404 döner (R-04); kullanıcıya aynı mesaj gösterilir.
    const notFound = page.error instanceof ApiError && page.error.status === 404;
    return <p>{notFound ? "Bu sayfa bulunamadı." : "Sayfa yüklenemedi."}</p>;
  }
  return (
    <article>
      <Breadcrumbs page={page.data} />
      <h1>{page.data.title}</h1>
    </article>
  );
}

function Breadcrumbs({ page }: Readonly<{ page: Page }>) {
  return (
    <nav aria-label="Konum" className="breadcrumbs">
      <ol>
        {page.breadcrumbs.map((crumb) => (
          <li key={crumb.id}>
            <Link to={`/pages/${crumb.id}`}>{crumb.title}</Link>
          </li>
        ))}
        <li aria-current="page">{page.title}</li>
      </ol>
    </nav>
  );
}
