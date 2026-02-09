"""
Resolution Registry — V3 Contract

Single authoritative gateway for construction knowledge,
geometry resolution, and default assumption policy.

NO PHYSICS
NO GUI
NO PROJECT STATE
"""

class ResolutionRegistry:
    """
    Central knowledge registry (read-only after init).

    This is a SERVICE CONTAINER, not a value object.
    """

    def __init__(self, presets, geometry):
        self.presets = presets
        self.geometry = geometry
