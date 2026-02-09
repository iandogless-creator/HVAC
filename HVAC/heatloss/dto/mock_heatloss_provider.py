"""
mock_heatloss_provider.py
------------------------

HVACgooee — Heat Loss Mock DTO Provider

Temporary development scaffold.

• No physics
• No engines
• Safe to delete
"""

from __future__ import annotations

from HVAC_legacy.heatloss.dto.heatloss_results_dto import (
    HeatLossResultsDTO,
    FabricLossItemDTO,
    VentilationLossDTO,
)


def get_mock_heatloss_results() -> HeatLossResultsDTO:
    return HeatLossResultsDTO(
        space_name="Living Room",
        design_temp_c=21.0,
        external_temp_c=-3.0,
        fabric_losses=[
            FabricLossItemDTO(
                element_name="External Wall",
                area_m2=18.5,
                u_value=0.28,
                heat_loss_w=145.0,
            ),
            FabricLossItemDTO(
                element_name="Window",
                area_m2=3.2,
                u_value=1.4,
                heat_loss_w=96.0,
            ),
        ],
        ventilation_loss=VentilationLossDTO(
            air_change_rate=0.5,
            volume_m3=62.0,
            heat_loss_w=88.0,
        ),
        total_heat_loss_w=329.0,
    )
