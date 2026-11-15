from typing import Literal

from pydantic import BaseModel

from kovan.application.health import ReadinessReport


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, Literal["up", "down"]]

    @classmethod
    def from_report(cls, report: ReadinessReport) -> "ReadinessResponse":
        return cls(
            status="ready" if report.ready else "not_ready",
            checks={name: "up" if ok else "down" for name, ok in report.checks.items()},
        )
