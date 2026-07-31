# ======================================================================
# H-S61-B2A — Proportioned pipe-material-family authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.core.materials.pipe_materials_library import get_material


DEFAULT_PROPORTIONED_PIPE_MATERIAL_FAMILY_V1 = "copper"

# Heating-water families available to the typed authority. PVC/ABS is
# deliberately excluded from this stage.
SUPPORTED_PROPORTIONED_PIPE_MATERIAL_FAMILIES_V1 = (
    "copper",
    "mlcp",
    "pex",
    "steel",
)

_MATERIAL_KEY_ALIASES_V1 = {
    "pex-al-pex": "pex",
    "pex_al_pex": "pex",
}


@dataclass(slots=True)
class ProportionedPipeMaterialFamilyIntentV1:
    """
    Persisted current/proposed material-family authority.

    The current family describes the committed pipework basis. The proposed
    family is an explicit designer intent for later H-S61-B2B candidate
    evaluation. Changing the proposed family does not commit pipe material,
    change a DN, or replace any hydraulic or balancing result.
    """

    schema: str = "proportioned_pipe_material_family_intent_v1"
    current_material_key: str = (
        DEFAULT_PROPORTIONED_PIPE_MATERIAL_FAMILY_V1
    )
    proposed_material_key: str = (
        DEFAULT_PROPORTIONED_PIPE_MATERIAL_FAMILY_V1
    )

    def __post_init__(self) -> None:
        self.current_material_key = normalise_pipe_material_family_key_v1(
            self.current_material_key
        )
        self.proposed_material_key = normalise_pipe_material_family_key_v1(
            self.proposed_material_key
        )

    @property
    def current_material_label(self) -> str:
        return pipe_material_family_label_v1(self.current_material_key)

    @property
    def proposed_material_label(self) -> str:
        return pipe_material_family_label_v1(self.proposed_material_key)

    @property
    def material_change_proposed(self) -> bool:
        return self.proposed_material_key != self.current_material_key

    def set_proposed_material_family(self, material_key: str) -> None:
        """Set preview intent only; never alter the committed family."""
        self.proposed_material_key = normalise_pipe_material_family_key_v1(
            material_key
        )

    def reset_proposed_material_family(self) -> None:
        self.proposed_material_key = self.current_material_key

    def to_dict(self) -> dict:
        return proportioned_pipe_material_family_intent_to_dict_v1(self)

    @classmethod
    def from_dict(
            cls,
            data: dict | None,
    ) -> "ProportionedPipeMaterialFamilyIntentV1":
        return proportioned_pipe_material_family_intent_from_dict_v1(data)


def normalise_pipe_material_family_key_v1(value: object) -> str:
    key = str(value or "").strip().lower()
    key = _MATERIAL_KEY_ALIASES_V1.get(key, key)
    if key not in SUPPORTED_PROPORTIONED_PIPE_MATERIAL_FAMILIES_V1:
        allowed = ", ".join(
            SUPPORTED_PROPORTIONED_PIPE_MATERIAL_FAMILIES_V1
        )
        raise ValueError(
            f"Unsupported Proportioned heating pipe material family: "
            f"{key or '—'}; expected one of {allowed}"
        )
    if get_material(key) is None:
        raise ValueError(
            f"Proportioned pipe material family is absent from the "
            f"authoritative material library: {key}"
        )
    return key


def pipe_material_family_label_v1(material_key: object) -> str:
    key = normalise_pipe_material_family_key_v1(material_key)
    material = get_material(key)
    assert material is not None
    return str(material.name)


def proportioned_pipe_material_family_intent_to_dict_v1(
        intent: ProportionedPipeMaterialFamilyIntentV1,
) -> dict:
    if not isinstance(intent, ProportionedPipeMaterialFamilyIntentV1):
        raise TypeError(
            "ProportionedPipeMaterialFamilyIntentV1 required"
        )
    return {
        "schema": intent.schema,
        "current_material_key": intent.current_material_key,
        "proposed_material_key": intent.proposed_material_key,
    }


def proportioned_pipe_material_family_intent_from_dict_v1(
        data: dict | None,
) -> ProportionedPipeMaterialFamilyIntentV1:
    if data is None:
        return ProportionedPipeMaterialFamilyIntentV1()
    if not isinstance(data, dict):
        raise TypeError(
            "Proportioned pipe-material-family intent must be a dictionary"
        )

    schema = str(
        data.get("schema")
        or "proportioned_pipe_material_family_intent_v1"
    ).strip()
    if schema != "proportioned_pipe_material_family_intent_v1":
        raise ValueError(
            "Unsupported Proportioned pipe-material-family intent schema"
        )

    current_key = data.get(
        "current_material_key",
        DEFAULT_PROPORTIONED_PIPE_MATERIAL_FAMILY_V1,
    )
    proposed_key = data.get("proposed_material_key", current_key)
    return ProportionedPipeMaterialFamilyIntentV1(
        schema=schema,
        current_material_key=current_key,
        proposed_material_key=proposed_key,
    )
