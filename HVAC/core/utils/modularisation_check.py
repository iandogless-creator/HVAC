"""
HVACgooee — Modularisation Boundary Diagnostics
===============================================

Purpose
-------
Provide developer-side utilities for validating:
- clean module boundaries,
- no cross-contamination between subsystems,
- correct dependency direction (core → specialised → GUI, not reversed),
- no monolithic sprawl.

This module is *not* used by end-users.
It is a development-time tool.

Philosophy
----------
HVACgooee is intentionally modular:
    core/
    heatloss/
    hydronics/
    fenestration/
    energy/
    gui/
    plugins/

This helper detects violations such as:
- GUI importing business-logic directly from non-GUI modules.
- hydronics importing GUI code.
- circular imports across subsystems.
- forbidden import directions.

Usage
-----
from HVAC.core.utils.modularisation_check import check_module_dependencies

errors = check_module_dependencies({
    "core": ["heatloss", "hydronics", "fenestration", "energy", "gui"],
    "heatloss": ["gui"],
    "hydronics": ["gui"],
    "fenestration": ["gui"],
    "energy": ["gui"],
})
if errors:
    print("Modularisation issues detected:")
    for e in errors:
        print(" -", e)

This module is deliberately conservative; it warns rather than fails.
"""

from __future__ import annotations
import pkgutil
import importlib
import inspect
import sys
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_modules(package_name: str) -> List[str]:
    """
    Return all modules inside a given package name.
    """
    modules = []
    try:
        package = importlib.import_module(package_name)
    except Exception:
        return modules

    if hasattr(package, "__path__"):
        for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            modules.append(modname)

    return modules


def _module_imports(module_name: str) -> List[str]:
    """
    Attempt to list modules imported by a given module.
    VERY conservative: inspects bytecode / source via module.__dict__.
    """
    imports = []
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return imports

    for name, obj in mod.__dict__.items():
        if inspect.ismodule(obj):
            imports.append(obj.__name__)

    return imports


# ---------------------------------------------------------------------------
# Main Diagnostic
# ---------------------------------------------------------------------------

def check_module_dependencies(allowed_imports: Dict[str, List[str]]) -> List[str]:
    """
    Check for violations of allowed import directions.

    allowed_imports structure:
        {
            "core": ["heatloss", "hydronics", ...],      # core may import these
            "heatloss": ["core"],                         # heatloss may import core
            ...
        }

    Returns:
        List of violation strings.
    """
    errors = []

    # Build module groups for mapping
    groups: Dict[str, List[str]] = {}
    for group in allowed_imports.keys():
        groups[group] = [
            m for m in _iter_modules(f"HVAC.{group}")
        ]

    # Check each module in each group
    for group, modules in groups.items():
        allowed = allowed_imports.get(group, [])
        allowed_prefixes = [f"HVAC.{g}" for g in allowed]

        for mod in modules:
            imported = _module_imports(mod)
            for imp in imported:
                if not imp.startswith("HVAC."):
                    continue  # external imports are fine

                # Determine which group the imported module belongs to
                target_group = None
                for g, gmods in groups.items():
                    if imp in gmods:
                        target_group = g
                        break

                if target_group is None:
                    continue

                # Allowed?
                if target_group not in allowed:
                    errors.append(
                        f"Illegal import: {mod} imports {imp} (from group '{target_group}') "
                        f"but '{group}' may only import: {allowed}"
                    )

    return errors


# ---------------------------------------------------------------------------
# Circular Import Detector (Optional)
# ---------------------------------------------------------------------------

def detect_circular_imports(packages: List[str]) -> List[Tuple[str, str]]:
    """
    Detect simple circular imports within HVAC.

    Returns list of tuples: (module_a, module_b)
    """
    circulars = []

    visited = set()
    stack = []

    def visit(mod_name: str):
        if mod_name in stack:
            circulars.append((stack[-1], mod_name))
            return
        if mod_name in visited:
            return

        visited.add(mod_name)
        stack.append(mod_name)

        try:
            imports = _module_imports(mod_name)
        except Exception:
            imports = []

        for i in imports:
            if i.startswith("HVAC."):
                visit(i)

        stack.pop()

    # Start scanning each package
    for pkg in packages:
        for mod in _iter_modules(pkg):
            visit(mod)

    return circulars
