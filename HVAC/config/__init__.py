"""
HVACgooee — Global Configuration Access (v1)

⚠️ CONFIG CONSUMPTION CONTRACT — READ BEFORE USING ⚠️

This package provides access to *global configuration defaults* only.

NON-NEGOTIABLE RULES:

1. Configuration is read ONCE at application startup.
2. Configuration provides:
   - UI preferences
   - startup defaults
   - paths and metadata
3. Configuration MUST NOT:
   - alter physics
   - affect solver behaviour
   - inject safety factors invisibly
   - encode engineering decisions
4. Engines (heat-loss, hydronics, physics solvers):
   ❌ MUST NOT import or read config
5. Job data (.hvac.json) ALWAYS overrides config.
6. Education/debug flags control VISIBILITY ONLY, never calculations.

If changing a config value can change a calculated result
without explicit user intent, this contract is violated.

When in doubt:
- make it job-scoped
- make it explicit
- pass it as a parameter

See:
docs/architecture/config_consumption_contract.md
"""
"""
HVACgooee — Configuration Package

This package exposes configuration loaders and schemas.

Do NOT import this package from engines or solvers.
"""

# Intentionally empty.
