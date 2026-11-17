"""Uygulamanın bağımlılıklarının hazır olup olmadığını raporlar (`/health/ready`)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from kovan.application.ports.system import ReadinessProbe


@dataclass(frozen=True)
class ReadinessReport:
    checks: Mapping[str, bool]

    @property
    def ready(self) -> bool:
        return all(self.checks.values())


class ReadinessService:
    def __init__(self, probes: Sequence[ReadinessProbe]) -> None:
        self._probes = tuple(probes)

    def check(self) -> ReadinessReport:
        return ReadinessReport(checks={probe.name: probe.is_ready() for probe in self._probes})
