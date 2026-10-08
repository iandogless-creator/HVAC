"""Pure-water density and dynamic viscosity; IAPWS SR6-08(2011).

Attribution: International Association for the Properties of Water and Steam,
Revised Supplementary Release on Properties of Liquid Water at 0.1 MPa,
September 2011, equations (2), (4), (7), Tables 1 and 4.
https://iapws.org/technical-guidance/release/LiquidWater.download

Reference-pressure approximation, NOT a fill-pressure or boiling assessment.
No glycol, heat capacity, heat transfer, or automatic engineering acceptance.
"""
from dataclasses import asdict, dataclass
import math

MODEL_ID = "iapws_sr6_2008_2011_water_rho_mu_v1"
TEMPERATURE_BASIS = "mean_design_flow_return_v1"


def water_properties_at_temperature_v1(temperature_c: float) -> tuple[float, float]:
    """Return (kg/m³, Pa·s) within the published -20..110°C range.

    Parts of this correlation range describe metastable liquid. Project
    resolution below deliberately uses only 5..95°C for both design inputs.
    """
    if (isinstance(temperature_c, bool)
            or not isinstance(temperature_c, (int, float))
            or not math.isfinite(temperature_c) or not -20 <= temperature_c <= 110):
        raise ValueError("Water correlation requires a finite temperature from -20 to 110°C.")
    temperature_k = float(temperature_c) + 273.15
    alpha = 10.0 / (593.0 - temperature_k)
    beta = 10.0 / (temperature_k - 232.0)
    a_terms = ((6744.58446, 4), (-222521.604, 5), (100231247.0, 7),
               (-1635521180.0, 8), (8322996580.0, 9))
    b_terms = (0.00578545292, -0.0153195665, 0.0311337859,
               -0.0423546241, 0.0338713507, -0.0119946761)
    volume = (461.51805 * 10 / 100000) * (
        0.0193763157 + sum(a * alpha**n for a, n in a_terms)
        + sum(b * beta**m for m, b in enumerate(b_terms, 1)))
    mu = 1e-6 * sum(a * (temperature_k / 300)**b for a, b in
                   ((280.68, -1.9), (511.45, -7.7), (61.131, -19.6), (0.45903, -40)))
    return 1 / volume, mu


@dataclass(frozen=True, slots=True)
class WaterHydraulicBasisV1:
    design_flow_temp_c: float
    design_return_temp_c: float
    temperature_c: float
    density_kg_m3: float
    dynamic_viscosity_Pa_s: float
    model_id: str = MODEL_ID
    temperature_basis: str = TEMPERATURE_BASIS
    fluid_key: str = "WATER"
    reference_pressure_Pa: float = 100000.0

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def basis_id(self) -> str:
        # Include both inputs: a changed delta-T may change carried mass flow
        # even when the mean, density and viscosity remain identical.
        return (f"{self.model_id}:{self.temperature_basis}:"
                f"{self.design_flow_temp_c:.17g}/{self.design_return_temp_c:.17g}")

    @property
    def description(self) -> str:
        return (f"Water at {self.temperature_c:g}°C mean "
                f"({self.design_flow_temp_c:g}/{self.design_return_temp_c:g}°C): "
                f"ρ {self.density_kg_m3:.3f} kg/m³; "
                f"μ {self.dynamic_viscosity_Pa_s * 1000:.4f} mPa·s. "
                "IAPWS, 0.1 MPa reference.")


def build_water_hydraulic_basis_v1(flow_c, return_c) -> WaterHydraulicBasisV1:
    for value in (flow_c, return_c):
        if (isinstance(value, bool) or not isinstance(value, (float, int))
                or not math.isfinite(value) or not 5 <= value <= 95):
            raise ValueError("Water basis needs Environment flow and return temperatures within 5–95°C.")
    if flow_c <= return_c:
        raise ValueError("Design flow temperature must be above design return temperature.")
    mean = (float(flow_c) + float(return_c)) / 2
    rho, mu = water_properties_at_temperature_v1(mean)
    return WaterHydraulicBasisV1(float(flow_c), float(return_c), mean, rho, mu)


def resolve_project_water_basis_v1(project) -> WaterHydraulicBasisV1:
    """Read-only project resolution. Missing/invalid inputs never use fallback."""
    env = getattr(project, "environment", None)
    return build_water_hydraulic_basis_v1(
        getattr(env, "design_flow_temp_c", None),
        getattr(env, "design_return_temp_c", None))


def water_hydraulic_basis_from_dict_v1(raw) -> WaterHydraulicBasisV1 | None:
    """Missing means legacy. Present but corrupt/unsupported evidence fails closed."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("Invalid frozen water basis.")
    basis = build_water_hydraulic_basis_v1(raw.get("design_flow_temp_c"),
                                          raw.get("design_return_temp_c"))
    if set(raw) != set(basis.to_dict()):
        raise ValueError("Incomplete or unsupported frozen water basis.")
    for key, expected in basis.to_dict().items():
        actual = raw[key]
        if isinstance(expected, str):
            valid = actual == expected
        else:
            valid = (not isinstance(actual, bool) and isinstance(actual, (float, int))
                     and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=0))
        if not valid:
            raise ValueError("Frozen water properties do not match their recorded model and temperatures.")
    return basis


def committed_water_basis_v1(project) -> WaterHydraulicBasisV1:
    """Validate current inputs against frozen evidence; never update a snapshot."""
    snapshot = getattr(project, "hydronic_proportioned_basis_snapshot", None)
    if snapshot is None:
        raise ValueError("Commit Proportioning to freeze the shared water basis.")
    authority = getattr(snapshot, "hydraulic_input_authority", None)
    frozen = getattr(authority, "fluid_basis", None)
    if not isinstance(frozen, WaterHydraulicBasisV1):
        raise ValueError("Legacy hydraulic snapshot has no shared water basis; recalculate and Recommit Proportioning.")
    water_hydraulic_basis_from_dict_v1(frozen.to_dict())
    if frozen != resolve_project_water_basis_v1(project):
        raise ValueError("Water temperature basis changed; recalculate, review and Recommit Proportioning.")
    return frozen
