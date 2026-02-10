"""
heatloss_service.py
-------------------

HVACgooee — Heat Loss Orchestration Service (v1)

Responsible for:
• Calling the heat-loss engine
• Converting results to DTOs
• Returning GUI-safe objects

No GUI imports.
"""

from __future__ import annotations

from HVAC.heatloss.adapters.engine_to_dto import build_heatloss_dto

# IMPORT YOUR REAL ENGINE HERE


def get_heatloss_results_for_space(space) :
    """
    Orchestrate heat-loss calculation for one space
    and return GUI-facing DTO.

    space:
        Domain Space object (not GUI)
    """

    engine_result = run_technical_heatloss(space)

    return build_heatloss_dto(engine_result)
