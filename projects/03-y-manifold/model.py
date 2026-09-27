"""Smooth, upright support-free 45° Y-manifold for the Bambu Lab P1S (mm)."""

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
INLET_1_REACH_MM = 150.0  # Overall height 240 mm; 15.8 mm shorter than before.
OUTLET_REACH_MM = 90.0   # Previous 105 mm shortened by 15 mm.
MAIN_LENGTH_MM = INLET_1_REACH_MM + OUTLET_REACH_MM
JUNCTION_Z_MM = OUTLET_REACH_MM
BRANCH_LENGTH_MM = 115.0
JUNCTION_ANGLE_DEG = 45.0
BOOLEAN_OVERRUN_MM = 1.0

MAIN_BODY_RADIUS_MM = 30.0
BRANCH_BODY_RADIUS_MM = 29.5
JUNCTION_BLEND_MM = 3.0

Z_AXIS = cq.Vector(0, 0, 1)
INLET_2_AXIS = cq.Vector(
    math.sin(math.radians(JUNCTION_ANGLE_DEG)), 0,
    math.cos(math.radians(JUNCTION_ANGLE_DEG)),
)
JUNCTION = cq.Vector(0, 0, JUNCTION_Z_MM)
INLET_2_MOUTH = JUNCTION + INLET_2_AXIS * BRANCH_LENGTH_MM


def _cylinder(radius: float, length: float, origin: cq.Vector, axis=Z_AXIS) -> cq.Solid:
    return cq.Solid.makeCylinder(radius, length, origin, axis)


def _cone(r1: float, r2: float, length: float, origin: cq.Vector, axis=Z_AXIS) -> cq.Solid:
    return cq.Solid.makeCone(r1, r2, length, origin, axis)


def _smooth_envelope() -> cq.Shape:
    """Revolved, smoothly tapered bodies with a rolling blend at the joint.

    Radii decrease toward the upper mouths. With the outlet on the plate,
    this avoids the downward ledges produced by projecting reinforcement bands.
    Stations are tailored to this 240 mm design; rerun overhang/fit tests after
    changing dimensions or blend radius.
    """
    radius = INLET_OD_MM / 2
    main = (
        cq.Workplane("XZ").moveTo(0, 0).lineTo(OUTLET_OD_MM / 2, 0)
        .lineTo(OUTLET_OD_MM / 2, SOCKET_LENGTH_MM)
        .spline([(MAIN_BODY_RADIUS_MM, 60)], tangents=[(0, 1), (0, 1)], includeCurrent=True)
        .lineTo(MAIN_BODY_RADIUS_MM, 165)
        .spline([(radius, 200)], tangents=[(0, 1), (0, 1)], includeCurrent=True)
        .lineTo(radius, MAIN_LENGTH_MM - LEAD_IN_MM)
        .lineTo(radius - LEAD_IN_MM, MAIN_LENGTH_MM)
        .lineTo(0, MAIN_LENGTH_MM).close().revolve().val()
    )
    branch = (
        cq.Workplane("XZ").moveTo(0, 0).lineTo(BRANCH_BODY_RADIUS_MM, 0)
        .lineTo(BRANCH_BODY_RADIUS_MM, 55)
        .spline([(radius, 75)], tangents=[(0, 1), (0, 1)], includeCurrent=True)
        .lineTo(radius, BRANCH_LENGTH_MM - LEAD_IN_MM)
        .lineTo(radius - LEAD_IN_MM, BRANCH_LENGTH_MM)
        .lineTo(0, BRANCH_LENGTH_MM).close().revolve().val()
        .rotate((0, 0, 0), (0, 1, 0), JUNCTION_ANGLE_DEG)
        .translate(JUNCTION)
    )
    united = main.fuse(branch).clean()
    # Intersection edges are the off-center spline curves. Revolved profile
    # seams lie on Y=0 and are deliberately excluded from the joint blend.
    joint_edges = [edge for edge in united.Edges()
                   if edge.geomType() == "BSPLINE" and abs(edge.Center().y) > 1]
    if len(joint_edges) != 4:
        raise ValueError("Unexpected junction topology; review the blend edge selection")
    return united.fillet(JUNCTION_BLEND_MM, joint_edges).clean()


def outer_envelope(reinforced: bool = True) -> cq.Shape:
    """Smooth reinforced exterior, or the minimal-wall reference for tests."""
    if reinforced:
        return _smooth_envelope()
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
        _cylinder(inlet_r, BRANCH_LENGTH_MM - LEAD_IN_MM, JUNCTION, INLET_2_AXIS),
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
        _cylinder(inlet_r, BRANCH_LENGTH_MM + BOOLEAN_OVERRUN_MM, JUNCTION, INLET_2_AXIS),
    ]
    return shapes[0].fuse(*shapes[1:]).clean()


def build() -> cq.Shape:
    if not 0 < LEAD_IN_MM < WALL_MM < INLET_OD_MM / 2:
        raise ValueError("Require lead-in < wall thickness < inlet radius")
    if not 0 < JUNCTION_ANGLE_DEG < 90:
        raise ValueError("Branch must lean upstream between 0 and 90 degrees")
    transition_end = SOCKET_LENGTH_MM + TRANSITION_LENGTH_MM
    if not transition_end < JUNCTION_Z_MM < MAIN_LENGTH_MM:
        raise ValueError("Junction must be above the socket transition and below input 1")
    # Keep the entire 35 mm straight mating region clear of the other branch.
    radius = INLET_OD_MM / 2
    angle = math.radians(JUNCTION_ANGLE_DEG)
    junction_reach = radius / math.sin(angle) + radius / math.tan(angle)
    if min(INLET_1_REACH_MM, BRANCH_LENGTH_MM) <= junction_reach + CONNECTION_LENGTH_MM + LEAD_IN_MM:
        raise ValueError("Lengthen the inlet(s) to leave their connection cuffs unobstructed")
    # Fuse all outer volumes, then cut the joined bores. Unioning hollow tubes
    # instead would leave pieces of the trunk wall across the branch passage.
    return outer_envelope().cut(flow_passage()).clean()
