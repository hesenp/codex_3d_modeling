"""Y-manifold with a perpendicular inlet curving to a 45° junction (mm)."""

import math

import cadquery as cq

NOMINAL_DIAMETER_MM = 2.25 * 25.4  # 57.15 mm
DIAMETRAL_CLEARANCE_MM = 0.5      # Confirmed: on diameter, not each side.
INLET_OD_MM = NOMINAL_DIAMETER_MM - DIAMETRAL_CLEARANCE_MM
OUTLET_ID_MM = NOMINAL_DIAMETER_MM + DIAMETRAL_CLEARANCE_MM
WALL_MM = 3.0
INLET_ID_MM = INLET_OD_MM - 2 * WALL_MM
OUTLET_OD_MM = OUTLET_ID_MM + 2 * WALL_MM

CONNECTION_LENGTH_MM = 35.0
LEAD_IN_MM = 0.75
SOCKET_LENGTH_MM = CONNECTION_LENGTH_MM + LEAD_IN_MM
TRANSITION_LENGTH_MM = 20.0
# Axial distances measured from the Y centerline junction to each mouth.
INLET_1_REACH_MM = 165.8  # Previous 115 mm + 2 inches (50.8 mm).
OUTLET_REACH_MM = 90.0   # Previous 105 mm shortened by 15 mm.
MAIN_LENGTH_MM = INLET_1_REACH_MM + OUTLET_REACH_MM
JUNCTION_Z_MM = OUTLET_REACH_MM
BRANCH_ROOT_LENGTH_MM = 72.0
BEND_RADIUS_MM = 65.0
JUNCTION_ANGLE_DEG = 45.0
INLET_ANGLE_DEG = 90.0
BOOLEAN_OVERRUN_MM = 1.0

Z_AXIS = cq.Vector(0, 0, 1)
BRANCH_ROOT_AXIS = cq.Vector(
    math.sin(math.radians(JUNCTION_ANGLE_DEG)), 0,
    math.cos(math.radians(JUNCTION_ANGLE_DEG)),
)
INLET_2_AXIS = cq.Vector(1, 0, 0)
JUNCTION = cq.Vector(0, 0, JUNCTION_Z_MM)
BEND_START = JUNCTION + BRANCH_ROOT_AXIS * BRANCH_ROOT_LENGTH_MM


def bend_point(angle_deg: float) -> cq.Vector:
    """Point on the circular centerline; tangent angle is measured from +Z."""
    initial = math.radians(JUNCTION_ANGLE_DEG)
    angle = math.radians(angle_deg)
    return BEND_START + cq.Vector(
        BEND_RADIUS_MM * (math.cos(initial) - math.cos(angle)), 0,
        BEND_RADIUS_MM * (math.sin(angle) - math.sin(initial)),
    )


BEND_END = bend_point(INLET_ANGLE_DEG)
INLET_2_MOUTH = BEND_END + INLET_2_AXIS * (CONNECTION_LENGTH_MM + LEAD_IN_MM)


def branch_path(tip_extension_mm: float = 0.0) -> cq.Wire:
    """Tangent-continuous 45° root, circular bend, and horizontal fitting cuff."""
    return cq.Wire.assembleEdges([
        cq.Edge.makeLine(JUNCTION, BEND_START),
        cq.Edge.makeThreePointArc(
            BEND_START, bend_point((JUNCTION_ANGLE_DEG + INLET_ANGLE_DEG) / 2), BEND_END
        ),
        cq.Edge.makeLine(BEND_END, INLET_2_MOUTH + INLET_2_AXIS * tip_extension_mm),
    ])


def _branch_volume(radius: float, tip_extension_mm: float = 0.0) -> cq.Shape:
    profile = cq.Plane(origin=JUNCTION, xDir=(0, 1, 0), normal=BRANCH_ROOT_AXIS)
    return (cq.Workplane(profile).circle(radius)
            .sweep(branch_path(tip_extension_mm), isFrenet=False).val())


def _cylinder(radius: float, length: float, origin: cq.Vector, axis=Z_AXIS) -> cq.Solid:
    return cq.Solid.makeCylinder(radius, length, origin, axis)


def _cone(r1: float, r2: float, length: float, origin: cq.Vector, axis=Z_AXIS) -> cq.Solid:
    return cq.Solid.makeCone(r1, r2, length, origin, axis)


def outer_envelope() -> cq.Shape:
    """Fused exterior, including entry bevels on the two male tips."""
    inlet_r = INLET_OD_MM / 2
    outlet_r = OUTLET_OD_MM / 2
    transition_end = SOCKET_LENGTH_MM + TRANSITION_LENGTH_MM
    shapes = [
        _cylinder(outlet_r, SOCKET_LENGTH_MM, cq.Vector()),
        _cone(outlet_r, inlet_r, TRANSITION_LENGTH_MM, cq.Vector(0, 0, SOCKET_LENGTH_MM)),
        _cylinder(inlet_r, MAIN_LENGTH_MM - transition_end - LEAD_IN_MM,
                  cq.Vector(0, 0, transition_end)),
        _cone(inlet_r, inlet_r - LEAD_IN_MM, LEAD_IN_MM,
              cq.Vector(0, 0, MAIN_LENGTH_MM - LEAD_IN_MM)),
        _branch_volume(inlet_r, -LEAD_IN_MM),
        _cone(inlet_r, inlet_r - LEAD_IN_MM, LEAD_IN_MM,
              INLET_2_MOUTH - INLET_2_AXIS * LEAD_IN_MM, INLET_2_AXIS),
    ]
    return shapes[0].fuse(*shapes[1:]).clean()


def flow_passage() -> cq.Shape:
    """One connected cutting volume, extended beyond all three port mouths."""
    inlet_r = INLET_ID_MM / 2
    outlet_r = OUTLET_ID_MM / 2
    transition_end = SOCKET_LENGTH_MM + TRANSITION_LENGTH_MM
    shapes = [
        _cylinder(outlet_r, SOCKET_LENGTH_MM + BOOLEAN_OVERRUN_MM,
                  cq.Vector(0, 0, -BOOLEAN_OVERRUN_MM)),
        # Female mouth expands toward Z=0 for an insertion lead-in.
        _cone(outlet_r + LEAD_IN_MM, outlet_r, LEAD_IN_MM, cq.Vector()),
        _cone(outlet_r, inlet_r, TRANSITION_LENGTH_MM, cq.Vector(0, 0, SOCKET_LENGTH_MM)),
        _cylinder(inlet_r, MAIN_LENGTH_MM - transition_end + BOOLEAN_OVERRUN_MM,
                  cq.Vector(0, 0, transition_end)),
        _branch_volume(inlet_r, BOOLEAN_OVERRUN_MM),
    ]
    return shapes[0].fuse(*shapes[1:]).clean()


def build() -> cq.Shape:
    if not 0 < LEAD_IN_MM < WALL_MM < INLET_OD_MM / 2:
        raise ValueError("Require lead-in < wall thickness < inlet radius")
    if not 0 < JUNCTION_ANGLE_DEG < INLET_ANGLE_DEG == 90:
        raise ValueError("Require an acute junction and a perpendicular connection")
    if BEND_RADIUS_MM <= INLET_OD_MM / 2:
        raise ValueError("Bend radius must exceed tube radius to avoid self-intersection")
    transition_end = SOCKET_LENGTH_MM + TRANSITION_LENGTH_MM
    if not transition_end < JUNCTION_Z_MM < MAIN_LENGTH_MM:
        raise ValueError("Junction must be above the socket transition and below input 1")
    # Keep the entire 35 mm straight mating region clear of the other branch.
    radius = INLET_OD_MM / 2
    angle = math.radians(JUNCTION_ANGLE_DEG)
    junction_reach = radius / math.sin(angle) + radius / math.tan(angle)
    if MAIN_LENGTH_MM - JUNCTION_Z_MM <= junction_reach + CONNECTION_LENGTH_MM + LEAD_IN_MM:
        raise ValueError("Lengthen input 1 to leave its connection cuff unobstructed")
    if BEND_START.x - radius * math.cos(angle) <= radius:
        raise ValueError("Lengthen the branch root so the bend clears the main tube")
    # Fuse all outer volumes, then cut the joined bores. Unioning hollow tubes
    # instead would leave pieces of the trunk wall across the branch passage.
    return outer_envelope().cut(flow_passage()).clean()
