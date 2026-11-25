import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <section>
      <h1>Sayfa bulunamadı</h1>
      <p>
        Aradığın adres yok. <Link to="/">Ana sayfaya dön</Link>.
      </p>
    </section>
  );
}
