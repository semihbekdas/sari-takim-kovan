from kovan.application.health import ReadinessService
from tests.fakes import FakeProbe


def test_report_is_ready_when_all_probes_are_up() -> None:
    service = ReadinessService([FakeProbe("database", ready=True), FakeProbe("qdrant", ready=True)])

    report = service.check()

    assert report.ready is True
    assert report.checks == {"database": True, "qdrant": True}


def test_report_is_not_ready_when_any_probe_is_down() -> None:
    service = ReadinessService(
        [FakeProbe("database", ready=True), FakeProbe("qdrant", ready=False)]
    )

    report = service.check()

    assert report.ready is False
    assert report.checks["qdrant"] is False
