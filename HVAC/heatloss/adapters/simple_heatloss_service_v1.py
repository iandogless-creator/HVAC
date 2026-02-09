"""
Simple Heat-Loss Service v1
---------------------------
QT = area × loss_rate × (Ti − To) / ΔT_ref

NOTE:
This is *deliberately simple* and explicit.
No geometry, no fabric, no side effects.
"""

from HVAC_legacy.heatloss.dto.simple_heatloss_input_dto import SimpleHeatLossInputDTO


class SimpleHeatLossServiceV1:
    @staticmethod
    def calculate_qt(dto: SimpleHeatLossInputDTO) -> float:
        delta_t = dto.ti_c - dto.to_c
        return dto.area_m2 * dto.loss_rate_w_m2 * (delta_t / 20.0)
