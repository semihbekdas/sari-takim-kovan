"""Arka plan indeksleme döngüsü (ADR-005): Uygulamayla aynı süreçte ~5 sn'de bir indeksleme turu.

Tur, veritabanı ve dış API çağrıları yaptığı için ayrı bir thread'de çalışır; böylece API
istekleri beklemez. Uygulama kapanırken `stop` olayı, turlar arasındaki beklemeyi hemen keser.
"""

import asyncio
import contextlib
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime

import structlog

from kovan.application.indexing_service import IndexRunReport

logger = structlog.get_logger(__name__)

RunOnce = Callable[[datetime], IndexRunReport]


def _utc_now() -> datetime:
    return datetime.now(UTC)


@contextlib.asynccontextmanager
async def running_index_loop(
    run_once: RunOnce, *, interval_seconds: float = 5
) -> AsyncIterator[asyncio.Task[None]]:
    """Döngüyü arka planda başlatır; çıkışta durdurur ve bitmesini bekler.

    Uygulama kapanırken o an süren tur yarıda kesilmez, bitmesi beklenir (en kötü durumda bir
    yapay zeka isteğinin zaman aşımı kadar).
    """
    stop = asyncio.Event()
    task = asyncio.create_task(run_index_loop(run_once, stop, interval_seconds=interval_seconds))
    try:
        yield task
    finally:
        stop.set()
        await task


async def run_index_loop(
    run_once: RunOnce,
    stop: asyncio.Event,
    *,
    interval_seconds: float = 5,
    clock: Callable[[], datetime] = _utc_now,
) -> None:
    """`stop` ayarlanana kadar her `interval_seconds` saniyede bir tur çalıştırır."""
    while not stop.is_set():
        await _run_round(run_once, clock())
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)


async def _run_round(run_once: RunOnce, now: datetime) -> None:
    try:
        report = await asyncio.to_thread(run_once, now)
    except Exception:
        # Beklenmeyen bir hata (ör. veritabanı geçici olarak kapalı) döngüyü kalıcı olarak
        # durdurmamalı. Hata gizlenmez: ayrıntısıyla loglanır, bir sonraki turda yeniden denenir.
        logger.exception("index_round_failed")
        return
    for error in report.unexpected_errors:
        logger.error("index_page_failed", exc_info=error)
    if report.did_work:
        logger.info(
            "index_round", indexed=report.indexed, removed=report.removed, failed=report.failed
        )
