# ======================================================================
# PERIMETER TERMINOLOGY (FUTURE-PROOFING — NO RUNTIME USE YET)
# ======================================================================
#
# IMPORTANT:
# Perimeter is NOT stored on RoomState.
# It is always derived from BoundarySegmentV1.
#
# Definitions (to remain stable across architecture evolution):
#
# gross_perimeter_m:
#     Sum of ALL segment lengths owned by the room.
#     (independent of boundary type)
#
# external_perimeter_m:
#     Sum of segment lengths where boundary_kind == EXTERNAL
#
# inter_room_perimeter_m:
#     Sum of segment lengths where boundary_kind == INTER_ROOM
#
# adiabatic_perimeter_m:
#     Sum of segment lengths where boundary_kind == ADIABATIC
#
# NOTE:
# These are NOT yet computed or used in Phase IV.
# They are defined here to stabilise terminology before expansion.
#
# FUTURE USES:
# - infiltration modelling (external exposure)
# - ψ-value linear thermal bridges
# - adjacency analytics
# - reporting / QA validation
#
# INVARIANT:
# All perimeter values must be derived ONLY from topology segments:
#
#     perimeter = Σ(segment.length_m)
#
# NEVER:
# - store perimeter on RoomState
# - compute directly from geometry (L, W, etc.)
#
# ======================================================================
🧠 Why this is exactly the right move

You are:

✔ freezing vocabulary before com