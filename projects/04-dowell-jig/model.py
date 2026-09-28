"""Flip-indexed dowel jig for a 1 x 0.75 inch board end (millimetres).

One M14 x 1 drill guide is installed in the printed body. The guide is at a
quarter-width position; rotating the jig 180 degrees on the board indexes the
same guide to the matching position on the other half of the end grain.
"""

import math

import cadquery as cq

# Requested actual outside dimensions of the board end.
BOARD_WIDTH_MM = 1.0 * 25.4
BOARD_THICKNESS_MM = 0.75 * 25.4

# Total diametral clearance around the nominal board dimensions.
BOARD_WIDTH_CLEARANCE_MM = 0.6
BOARD_THICKNESS_CLEARANCE_MM = 0.5
CAVITY_WIDTH_MM = BOARD_WIDTH_MM + BOARD_WIDTH_CLEARANCE_MM
CAVITY_THICKNESS_MM = BOARD_THICKNESS_MM + BOARD_THICKNESS_CLEARANCE_MM

SIDE_WALL_MM = 4.0
ROOF_MM = 10.0
SOCKET_DEPTH_MM = 25.0
TOTAL_HEIGHT_MM = ROOF_MM + SOCKET_DEPTH_MM
OUTER_WIDTH_MM = CAVITY_WIDTH_MM + 2 * SIDE_WALL_MM
OUTER_THICKNESS_MM = CAVITY_THICKNESS_MM + 2 * SIDE_WALL_MM
OUTER_EDGE_FILLET_MM = 1.5

DRILL_DIAMETER_MM = 6.0
GUIDE_BODY_DIAMETER_MM = 16.0
GUIDE_THREAD_MAJOR_DIAMETER_MM = 14.0
GUIDE_THREAD_PITCH_MM = 1.0
GUIDE_THREAD_LENGTH_MM = 10.0

# FDM allowance applied on diameter to both the internal-thread crest and root.
THREAD_DIAMETRAL_CLEARANCE_MM = 0.45
THREAD_MAJOR_DIAMETER_MM = GUIDE_THREAD_MAJOR_DIAMETER_MM + THREAD_DIAMETRAL_CLEARANCE_MM
# ISO metric basic internal minor diameter D1 = D - 1.082532 P, enlarged by
# the same diametral allowance. The resulting 60-degree groove is printable
# while retaining useful engagement with the metal external thread.
THREAD_MINOR_DIAMETER_MM = (
    GUIDE_THREAD_MAJOR_DIAMETER_MM
    - 1.082532 * GUIDE_THREAD_PITCH_MM
    + THREAD_DIAMETRAL_CLEARANCE_MM
)
THREAD_LEAD_IN_MM = 0.8
BOOLEAN_OVERRUN_MM = 0.4

# Quarter points across the one-inch dimension give symmetric dowel locations.
HOLE_EDGE_OFFSET_MM = BOARD_WIDTH_MM / 4
GUIDE_X_MM = -BOARD_WIDTH_MM / 2 + HOLE_EDGE_OFFSET_MM
GUIDE_Y_MM = 0.0


def dowel_centers_from_left_edge() -> tuple[float, float]:
    """Return the two board-relative centers made before and after flipping."""
    return (HOLE_EDGE_OFFSET_MM, BOARD_WIDTH_MM - HOLE_EDGE_OFFSET_MM)


def _outer_shell() -> cq.Shape:
    body = (
        cq.Workplane("XY")
        .box(OUTER_WIDTH_MM, OUTER_THICKNESS_MM, TOTAL_HEIGHT_MM,
             centered=(True, True, False))
        .val()
    )
    vertical_edges = [
        edge for edge in body.Edges()
        if abs(edge.tangentAt().z) > 0.99
    ]
    return body.fillet(OUTER_EDGE_FILLET_MM, vertical_edges)


def _board_cavity() -> cq.Shape:
    """Open socket; its lower face is the board-end registration shoulder."""
    return cq.Workplane("XY", origin=(0, 0, ROOF_MM)).box(
        CAVITY_WIDTH_MM,
        CAVITY_THICKNESS_MM,
        SOCKET_DEPTH_MM + BOOLEAN_OVERRUN_MM,
        centered=(True, True, False),
    ).val()


def _thread_groove() -> cq.Shape:
    """Swept 60-degree female-thread groove around the minor-diameter bore."""
    pitch = GUIDE_THREAD_PITCH_MM
    minor_radius = THREAD_MINOR_DIAMETER_MM / 2
    major_radius = THREAD_MAJOR_DIAMETER_MM / 2
    radial_depth = major_radius - minor_radius
    half_width = radial_depth / math.tan(math.radians(60))
    start_z = -BOOLEAN_OVERRUN_MM
    height = ROOF_MM + 2 * BOOLEAN_OVERRUN_MM

    helix = cq.Wire.makeHelix(
        pitch,
        height,
        minor_radius,
        cq.Vector(GUIDE_X_MM, GUIDE_Y_MM, start_z),
        cq.Vector(0, 0, 1),
    )
    tangent = cq.Vector(0, 2 * math.pi * minor_radius, pitch).normalized()
    section_plane = cq.Plane(
        origin=(GUIDE_X_MM + minor_radius, GUIDE_Y_MM, start_z),
        xDir=(1, 0, 0),
        normal=tangent,
    )
    return (
        cq.Workplane(section_plane)
        .moveTo(-0.08, -half_width)
        .lineTo(radial_depth, 0)
        .lineTo(-0.08, half_width)
        .close()
        .sweep(helix, isFrenet=True)
        .val()
    )


def _thread_core() -> cq.Shape:
    minor_radius = THREAD_MINOR_DIAMETER_MM / 2
    return cq.Solid.makeCylinder(
        minor_radius,
        ROOF_MM + 2 * BOOLEAN_OVERRUN_MM,
        cq.Vector(GUIDE_X_MM, GUIDE_Y_MM, -BOOLEAN_OVERRUN_MM),
    )


def _thread_lead_in() -> cq.Shape:
    return cq.Solid.makeCone(
        THREAD_MAJOR_DIAMETER_MM / 2 + 0.45,
        THREAD_MINOR_DIAMETER_MM / 2,
        THREAD_LEAD_IN_MM + BOOLEAN_OVERRUN_MM,
        cq.Vector(GUIDE_X_MM, GUIDE_Y_MM, -BOOLEAN_OVERRUN_MM),
    )


def build() -> cq.Shape:
    """Build the single-piece jig body without writing output files."""
    if GUIDE_THREAD_LENGTH_MM != ROOF_MM:
        raise ValueError("Roof must match the guide's threaded length")
    if not 0 < THREAD_MINOR_DIAMETER_MM < THREAD_MAJOR_DIAMETER_MM:
        raise ValueError("Thread diameters must be positive and ordered")
    if HOLE_EDGE_OFFSET_MM <= DRILL_DIAMETER_MM / 2:
        raise ValueError("Dowel hole breaks through the board edge")
    if SIDE_WALL_MM <= OUTER_EDGE_FILLET_MM:
        raise ValueError("Outer fillet must remain smaller than the side wall")

    # Sequential cuts avoid retained coincident faces where the core cylinder
    # and helical cutter overlap; those faces can become non-manifold in STL.
    return (
        _outer_shell()
        .cut(_board_cavity())
        .cut(_thread_core())
        .cut(_thread_groove())
        .cut(_thread_lead_in())
        .clean()
    )
