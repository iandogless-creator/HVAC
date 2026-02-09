# hvac/flowrate.py
"""
LEGACY / ESTIMATION ONLY

Velocity-based pipe sizing.
Not suitable for final hydronic design.
"""


from math import pi, sqrt

def PipeSizeFunc(flow, velocity=1.5):
    """Calculate pipe diameter from flow (m³/s) and velocity (m/s)."""
    area = flow / velocity
    diameter = sqrt(4 * area / pi)
    return diameter

def PipeSizeFromFlow(flow_list):
    """Calculate diameters for a list of flows."""
    return [PipeSizeFunc(f) for f in flow_list]

if __name__ == "__main__":
    # Example standalone usage
    flows = [0.1, 0.3, 0.5]
    diameters = PipeSizeFromFlow(flows)
    print("Pipe diameters (m):", diameters)
