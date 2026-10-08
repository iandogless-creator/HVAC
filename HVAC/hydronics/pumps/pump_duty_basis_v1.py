"""H-S73-B: explicit route/valve inputs and separately accepted pump duty."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class PumpRouteEquipmentV1:
    route_id: str
    pressure_Pa: float
    source_note: str


@dataclass(frozen=True, slots=True)
class PumpPointKvV1:
    point_id: str
    operating_kv: float | None


@dataclass(frozen=True, slots=True)
class PumpDutyBasisV1:
    preview_basis_fingerprint: str
    routes: tuple[PumpRouteEquipmentV1, ...]
    points: tuple[PumpPointKvV1, ...]
    review_note: str
    reviewed: bool

    def to_dict(self) -> dict:
        return {"schema": "pump_duty_basis_v1", **asdict(self)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get("schema") != "pump_duty_basis_v1":
            return None
        try:
            # Preserve invalid values for readiness checks; never turn strings
            # such as "false" into accepted Boolean intent or insert assumptions.
            basis = cls(
                preview_basis_fingerprint=data["preview_basis_fingerprint"],
                routes=tuple(PumpRouteEquipmentV1(**r) for r in data["routes"]),
                points=tuple(PumpPointKvV1(**r) for r in data["points"]),
                review_note=data["review_note"], reviewed=data["reviewed"],
            )
            if (not isinstance(basis.preview_basis_fingerprint, str)
                    or not isinstance(basis.review_note, str)
                    or type(basis.reviewed) is not bool
                    or any(not isinstance(r.route_id, str) or not isinstance(r.source_note, str)
                           for r in basis.routes)
                    or any(not isinstance(p.point_id, str) for p in basis.points)):
                return None
            return basis
        except (KeyError, TypeError, ValueError):
            return None


@dataclass(frozen=True, slots=True)
class PumpDutyAcceptanceV1:
    basis_fingerprint: str
    flow_m3_h: float
    pressure_Pa: float
    head_m: float
    review_note: str

    def to_dict(self) -> dict:
        return {"schema": "pump_duty_acceptance_v1", **asdict(self)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get("schema") != "pump_duty_acceptance_v1":
            return None
        try:
            return cls(**{k: data[k] for k in cls.__dataclass_fields__})
        except (KeyError, TypeError, ValueError):
            return None
