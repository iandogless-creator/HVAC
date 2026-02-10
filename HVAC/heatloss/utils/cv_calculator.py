from HVAC.gui_v2.common.heatloss_constants import FABRIC_CV_DIVISOR


def calculate_cv(
    *,
    sum_fabric_heat_loss_w: float,
    sum_fabric_area_m2: float,
) -> float:
    """
    Canonical Cv definition (LOCKED v1):

        Cv = ΣQf / (ΣA × 4.8)

    Raises:
        ValueError if area is zero or negative.
    """
    if sum_fabric_area_m2 <= 0:
        raise ValueError("ΣArea must be > 0 to compute Cv")

    return sum_fabric_heat_loss_w / (
        sum_fabric_area_m2 * FABRIC_CV_DIVISOR
    )
