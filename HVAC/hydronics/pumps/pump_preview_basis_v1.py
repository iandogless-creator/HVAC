"""H-S73-A: designer intent for a preliminary, committed-snapshot pump review."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class PumpPreviewBasisV1:
    density_kg_m3: float
    additional_common_loss_Pa: float
    head_margin_percent: float
    source_note: str
    snapshot_fingerprint: str

    def to_dict(self) -> dict:
        return {"schema": "pump_preview_basis_v1", **asdict(self)}

    @classmethod
    def from_dict(cls, data: object):
        # Preserve supplied intent, including incomplete legacy data, for the
        # controller to explain. Never silently repair engineering inputs.
        if not isinstance(data, dict):
            return None
        return cls(**{key: data.get(key) for key in cls.__dataclass_fields__})
