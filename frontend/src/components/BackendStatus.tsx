import { useQuery } from "@tanstack/react-query";

import { getHealth } from "../api/health";

/** Sol menünün altında backend'e ulaşılıp ulaşılamadığını gösterir. */
export function BackendStatus() {
  const { isPending, isError } = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => getHealth(signal),
    refetchInterval: 30_000,
  });

  if (isPending) {
    return <p className="backend-status">Sunucu: kontrol ediliyor…</p>;
  }
  if (isError) {
    return <p className="backend-status backend-status--down">Sunucu: bağlanılamadı</p>;
  }
  return <p className="backend-status backend-status--up">Sunucu: bağlı</p>;
}
