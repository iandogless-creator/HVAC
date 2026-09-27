"""Pure pump preview arithmetic. Inputs are validated by the controller."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PumpPreviewNumbersV1:
    flow_m3_h: float
    pressure_Pa: float
    head_m: float


def run_pump_preview_v1(*, mass_flow_kg_s: float, density_kg_m3: float,
                        pipework_pressure_Pa: float,
                        additional_common_loss_Pa: float,
                        head_margin_percent: float) -> PumpPreviewNumbersV1:
    pressure = (pipework_pressure_Pa + additional_common_loss_Pa) * (
        1.0 + head_margin_percent / 100.0
    )
    return PumpPreviewNumbersV1(
        flow_m3_h=mass_flow_kg_s / density_kg_m3 * 3600.0,
        pressure_Pa=pressure,
        head_m=pressure / (density_kg_m3 * 9.81),
    )
