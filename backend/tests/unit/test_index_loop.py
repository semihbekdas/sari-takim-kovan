"""İndeksleme döngüsü: sahte tur fonksiyonu, gerçek asyncio zamanlayıcısı ve stop olayıyla."""

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
import structlog
from structlog.testing import capture_logs

from kovan.application.indexing_service import IndexRunReport
from kovan.infrastructure.index_loop import run_index_loop

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
NOTHING_DONE = IndexRunReport()


@pytest.fixture(autouse=True)
def default_structlog_config() -> Iterator[None]:
    """Başka testlerin ayarladığı log seviyesi (WARNING) buradaki info logunu gizlemesin.

    Test bitince önceki ayar geri konur; sonraki testler etkilenmez.
    """
    saved = structlog.get_config()
    structlog.reset_defaults()
    yield
    structlog.configure(**saved)


class FakeRounds:
    def __init__(self, report: IndexRunReport = NOTHING_DONE, *, fail_first: bool = False) -> None:
        self.calls: list[datetime] = []
        self._report = report
        self._fail_first = fail_first

    def __call__(self, now: datetime) -> IndexRunReport:
        self.calls.append(now)
        if self._fail_first and len(self.calls) == 1:
            raise RuntimeError("veritabanı geçici olarak kapalı")
        return self._report


def _run_loop_until(rounds: FakeRounds, *, rounds_needed: int, interval: float = 0.001) -> None:
    """Döngüyü başlatır, istenen tur sayısına ulaşınca durdurur. 2 sn'de bitmezse test düşer."""

    async def scenario() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(
            run_index_loop(rounds, stop, interval_seconds=interval, clock=lambda: NOW)
        )
        while len(rounds.calls) < rounds_needed:
            await asyncio.sleep(0.001)
        stop.set()
        await task

    asyncio.run(asyncio.wait_for(scenario(), timeout=2))


def test_loop_runs_rounds_until_stopped() -> None:
    rounds = FakeRounds()

    _run_loop_until(rounds, rounds_needed=3)

    assert rounds.calls[:3] == [NOW, NOW, NOW]


def test_stop_interrupts_the_wait_between_rounds() -> None:
    rounds = FakeRounds()

    # Bekleme 60 sn; stop beklemeyi kesmeseydi test 2 sn'lik sınırı aşıp düşerdi.
    _run_loop_until(rounds, rounds_needed=1, interval=60)

    assert len(rounds.calls) == 1


def test_unexpected_error_is_logged_and_loop_continues() -> None:
    rounds = FakeRounds(fail_first=True)

    with capture_logs() as logs:
        _run_loop_until(rounds, rounds_needed=2)

    assert len(rounds.calls) >= 2
    failures = [entry for entry in logs if entry["event"] == "index_round_failed"]
    assert len(failures) == 1
    assert failures[0]["log_level"] == "error"


def test_only_rounds_that_did_work_are_logged() -> None:
    with capture_logs() as idle_logs:
        _run_loop_until(FakeRounds(), rounds_needed=2)
    with capture_logs() as busy_logs:
        _run_loop_until(FakeRounds(IndexRunReport(indexed=2, failed=1)), rounds_needed=1)

    assert idle_logs == []
    assert {
        "event": "index_round",
        "log_level": "info",
        "indexed": 2,
        "removed": 0,
        "failed": 1,
    } in busy_logs


def test_unexpected_page_errors_are_logged_with_details() -> None:
    error = ValueError("EMBEDDING_DIM yanlış")
    rounds = FakeRounds(IndexRunReport(failed=1, unexpected_errors=(error,)))

    with capture_logs() as logs:
        _run_loop_until(rounds, rounds_needed=1)

    failures = [entry for entry in logs if entry["event"] == "index_page_failed"]
    assert len(failures) == 1
    assert failures[0]["exc_info"] is error
    assert failures[0]["log_level"] == "error"
