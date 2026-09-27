"""A 1 × 2 × 3 cm solid rectangular block; all code dimensions are mm."""

import cadquery as cq

WIDTH_MM = 10.0
DEPTH_MM = 20.0
HEIGHT_MM = 30.0


def build() -> cq.Workplane:
    return cq.Workplane("XY").box(
        WIDTH_MM, DEPTH_MM, HEIGHT_MM, centered=(True, True, False)
    )
