"""Load project models and inspect exact CAD geometry (millimetres)."""

import importlib.util
from pathlib import Path

import cadquery as cq
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib


def as_shape(model: cq.Workplane | cq.Shape) -> cq.Shape:
    if isinstance(model, cq.Workplane):
        shapes = model.vals()
        if not shapes or not all(isinstance(item, cq.Shape) for item in shapes):
            raise ValueError("Expected a Workplane containing shapes")
        return cq.Compound.makeCompound(shapes) if len(shapes) > 1 else shapes[0]
    if isinstance(model, cq.Shape):
        return model
    raise TypeError("build() must return a CadQuery Workplane or Shape")


def load_model(path: str | Path) -> cq.Shape:
    """Execute a trusted local model.py exposing a side-effect-free build()."""
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("cadquery_project_model", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load Python model: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return as_shape(module.build())


def inspect_shape(model: cq.Workplane | cq.Shape) -> dict:
    shape = as_shape(model)
    # CadQuery's default box may use cached tessellation after export/render,
    # inflating curved-part dimensions by the mesh deflection. Measure geometry.
    bounds = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped, bounds, False, False)
    xmin, ymin, zmin, xmax, ymax, zmax = bounds.Get()
    return {
        "units": "mm",
        "valid": shape.isValid(),
        "solids": len(shape.Solids()),
        "size_mm": [xmax - xmin, ymax - ymin, zmax - zmin],
        "min_mm": [xmin, ymin, zmin],
        "max_mm": [xmax, ymax, zmax],
        "volume_mm3": shape.Volume(),
    }


def require_solid(model: cq.Workplane | cq.Shape) -> cq.Shape:
    shape = as_shape(model)
    info = inspect_shape(shape)
    if not info["valid"] or info["solids"] != 1 or info["volume_mm3"] <= 0:
        raise ValueError(f"Expected one valid, positive-volume solid: {info}")
    return shape
