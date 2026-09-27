"""Export a solid with explicit mesh tolerances and millimetre units."""

from pathlib import Path

import cadquery as cq

from cadquery_helper.models import require_solid

LINEAR_TOLERANCE_MM = 0.01
ANGULAR_TOLERANCE_RAD = 0.1


def export_model(model: cq.Workplane | cq.Shape, directory: Path, name: str) -> list[Path]:
    shape = require_solid(model)
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / f"{name}.{extension}" for extension in ("stl", "3mf", "step")]
    success = shape.exportStl(
        str(paths[0]), tolerance=LINEAR_TOLERANCE_MM,
        angularTolerance=ANGULAR_TOLERANCE_RAD, relative=False, ascii=False,
    )
    if not success:
        raise RuntimeError(f"STL export failed: {paths[0]}")
    for path in paths[1:]:
        cq.exporters.export(
            shape, str(path), tolerance=LINEAR_TOLERANCE_MM,
            angularTolerance=ANGULAR_TOLERANCE_RAD, unit="MM",
        )
    return paths
