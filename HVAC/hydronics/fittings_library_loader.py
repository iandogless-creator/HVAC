"""
fittings_library_loader.py
--------------------------

Load fittings from SQLite DB into Python dictionaries.

Supports:
    - Complexity levels: BASIC / ADVANCED / PRO
    - Optional manufacturer filter
"""

from __future__ import annotations

from typing import Dict, Literal, Optional
import sqlite3
from pathlib import Path

from HVAC.hydronics.hydronics_controller import FittingDefinition

Complexity = Literal["BASIC", "ADVANCED", "PRO"]

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "fittings"
DB_PATH = DATA_DIR / "fittings.db"


def load_fittings(
    complexity: Complexity,
    manufacturer: Optional[str] = None,
) -> Dict[str, FittingDefinition]:
    """
    Load fittings into a dict: code -> FittingDefinition.

    complexity:
        BASIC    -> BASIC only
        ADVANCED -> BASIC + ADVANCED
        PRO      -> all rows

    manufacturer:
        None     -> all manufacturers
        "GENERIC" or any name -> filter on that manufacturer
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Build WHERE clauses
    where_clauses = []
    params: list = []

    if complexity == "BASIC":
        where_clauses.append("complexity = 'BASIC'")
    elif complexity == "ADVANCED":
        where_clauses.append("complexity IN ('BASIC', 'ADVANCED')")
    else:  # PRO
        # all complexities
        pass

    if manufacturer:
        where_clauses.append("manufacturer = ?")
        params.append(manufacturer)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = (
        "SELECT code, description, category, size_min, size_max, k_value, complexity, manufacturer "
        "FROM fittings "
        f"{where_sql}"
    )

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    lib: Dict[str, FittingDefinition] = {}

    for code, desc, cat, smin, smax, kval, comp, manuf in rows:
        size_hint = f"{smin}-{smax}"
        fd = FittingDefinition(
            code=code,
            description=f"{desc} ({manuf})",
            category=cat,
            k_value=float(kval),
            size_hint=size_hint,
        )
        lib[code] = fd

    return lib
