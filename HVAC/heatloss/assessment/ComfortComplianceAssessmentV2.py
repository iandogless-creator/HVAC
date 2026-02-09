cv_k: float
"""
Comfort uplift coefficient (K).

Defined as:
    Cv = sumQf / (sumArea * comfort_factor)

Represents additional air temperature required
to maintain TEI due to fabric surface heat pull.
"""
cv_basis: str = "fabric_only_internal_surface"
tai_c: float
tei_c: float
