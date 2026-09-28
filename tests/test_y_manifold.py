"""Verify mating sizes, a straight 45° branch, printer fit, open bores, and exports."""

import importlib.util
import math
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
import pytest
import trimesh

from cadquery_helper.export import export_model
from cadquery_helper.models import inspect_shape, require_solid

MODEL_PATH = Path(__file__).resolve().parents[1] / "projects/03-y-manifold/model.py"


@pytest.fixture(scope="module")
def model():
    spec = importlib.util.spec_from_file_location("y_manifold", MODEL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def shape(model):
    return require_solid(model.build())


def test_fit_diameters_and_wall(shape, model):
    """Measure sections through actual geometry, rather than only constants."""
    stations = [
        (cq.Vector(0, 0, model.MAIN_LENGTH_MM - 20), cq.Vector(0, 0, 1), [50.15, 56.15]),
        (model.INLET_2_MOUTH - model.INLET_2_AXIS * 15, model.INLET_2_AXIS, [50.15, 56.15]),
        (cq.Vector(0, 0, 15), cq.Vector(0, 0, 1), [58.15, 64.15]),
    ]
    for center, axis, expected in stations:
        plane = cq.Plane(origin=center, normal=axis)
        section = cq.Workplane(plane).newObject([shape]).section()
        # The branch section plane may also intersect the trunk; select the
        # circular edges centered on the intended port axis.
        diameters = sorted(2 * edge.radius() for edge in section.edges().vals()
                           if edge.geomType() == "CIRCLE"
                           and (edge.arcCenter() - center).Length < 1e-5)
        assert diameters == pytest.approx(expected, abs=1e-5)
        assert (diameters[1] - diameters[0]) / 2 == pytest.approx(3.0)


def test_layout_and_unblocked_passages(shape, model):
    assert math.degrees(math.acos(model.INLET_2_AXIS.dot(model.Z_AXIS))) == pytest.approx(45)
    bounds = shape.BoundingBox()
    assert bounds.zmin == pytest.approx(0, abs=1e-6)
    assert bounds.zmax == pytest.approx(240.0, abs=1e-6)
    assert model.JUNCTION.z - bounds.zmin == pytest.approx(90.0, abs=1e-6)
    assert bounds.zmax - model.JUNCTION.z == pytest.approx(150.0, abs=1e-6)
    assert bounds.ylen == pytest.approx(model.OUTLET_OD_MM, abs=1e-6)
    solid = shape.Solids()[0]
    # Probe each full bore with an independent cylinder to catch leftover septa.
    probes = [
        cq.Solid.makeCylinder(24.95, model.MAIN_LENGTH_MM + 2, (0, 0, -1)),
        cq.Solid.makeCylinder(24.95, model.BRANCH_LENGTH_MM + 1,
                             model.JUNCTION, model.INLET_2_AXIS),
        cq.Solid.makeCylinder(28.95, 34, (0, 0, 1)),
    ]
    for probe in probes:
        assert shape.intersect(probe).Volume() == pytest.approx(0, abs=1e-6)
    passage = model.flow_passage()
    assert passage.isValid() and len(passage.Solids()) == 1
    # Model contains exactly the exterior minus the connected passage.
    exterior = model.outer_envelope()
    # Smooth spline/fillet surfaces require tighter integration than the
    # default to compare the difference of two much larger volumes.
    assert shape.Volume(tol=1e-9) == pytest.approx(
        exterior.Volume(tol=1e-9)
        - exterior.intersect(passage).Volume(tol=1e-9), rel=1e-7
    )
    # Material remains in all straight connection cuffs, for the full 35 mm.
    for distance in (1, 17.5, 34.9):
        assert solid.isInside((27, 0, model.MAIN_LENGTH_MM - 0.75 - distance))
        p = model.INLET_2_MOUTH - model.INLET_2_AXIS * (0.75 + distance) + cq.Vector(0, 27, 0)
        assert solid.isInside(p)
        assert solid.isInside((30, 0, 0.75 + distance))


def test_lead_ins(shape, model):
    solid = shape.Solids()[0]
    # 0.75 mm entry bevels ease insertion without changing the straight fit size.
    assert not solid.isInside((27.7, 0, model.MAIN_LENGTH_MM - 0.1))
    assert solid.isInside((27.7, 0, model.MAIN_LENGTH_MM - 1.0))
    assert not solid.isInside((29.4, 0, 0.1))
    assert solid.isInside((29.4, 0, 1.0))
    for distance, inside in [(0.1, False), (1.0, True)]:
        point = model.INLET_2_MOUTH - model.INLET_2_AXIS * distance + cq.Vector(0, 27.7, 0)
        assert solid.isInside(point) == inside


def test_p1s_build_envelope(shape, model):
    # Conservative design target inside the advertised 256 mm cube, leaving
    # room around the centered model and 16 mm below nominal maximum height.
    info = inspect_shape(shape)
    assert info["size_mm"][1:] == pytest.approx([model.OUTLET_OD_MM, 240], abs=1e-5)
    assert info["min_mm"][2] == pytest.approx(0, abs=1e-6)
    assert info["size_mm"][0] + 20 < 256  # 10 mm allowance each side
    assert info["size_mm"][1] + 20 < 256
    assert info["size_mm"][2] <= 240.0 + 1e-6


def test_manifold_exports(shape, tmp_path):
    before = inspect_shape(shape)
    expected_bounds = before["size_mm"]
    for path in export_model(shape, tmp_path, "y-manifold"):
        if path.suffix == ".step":
            restored = require_solid(cq.importers.importStep(str(path)))
            assert restored.Volume(tol=1e-9) == pytest.approx(shape.Volume(tol=1e-9), rel=1e-6)
            continue
        mesh = trimesh.load(str(path), force="mesh")
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert len(mesh.split()) == 1
        assert mesh.volume == pytest.approx(shape.Volume(), rel=0.002)
        assert np.allclose(mesh.extents, expected_bounds, atol=0.03)
        if path.suffix == ".3mf":
            with ZipFile(path) as archive:
                xml_path = next(name for name in archive.namelist() if name.endswith(".model"))
                assert ET.fromstring(archive.read(xml_path)).attrib["unit"] == "millimeter"
    # Reports must not inflate once OCCT caches a curved part's triangulation.
    after = inspect_shape(shape)
    for key in ("size_mm", "min_mm", "max_mm"):
        assert after[key] == pytest.approx(before[key], abs=1e-6)


def test_smooth_reinforcement_preserves_connections_and_bores(shape, model):
    plain = model.outer_envelope(reinforced=False).cut(model.flow_passage()).clean()
    added = shape.cut(plain)
    assert added.Volume() > 1000  # Real additional material, not cosmetic lines.
    assert plain.cut(shape).Volume() == pytest.approx(0, abs=1e-6)
    assert added.intersect(model.flow_passage()).Volume() == pytest.approx(0, abs=1e-6)
    # Both male fittings remain clear over their full mating length, including
    # space immediately outside the nominal OD; the female socket is untouched.
    for origin, axis in [
        (cq.Vector(0, 0, model.MAIN_LENGTH_MM - 35.75), model.Z_AXIS),
        (model.INLET_2_MOUTH - model.INLET_2_AXIS * 35.75, model.INLET_2_AXIS),
        (cq.Vector(0, 0, 0), model.Z_AXIS),
    ]:
        clearance = cq.Solid.makeCylinder(33, 35.75, origin, axis)
        assert added.intersect(clearance).Volume() == pytest.approx(0, abs=1e-6)
    # Distributed body thickening replaces projecting ribs and gussets.
    solid = shape.Solids()[0]
    for point in [(-29.5, 0, 110), (0, 29.5, 110), (0, -29.5, 110)]:
        assert solid.isInside(point)
        assert not plain.Solids()[0].isInside(point)



def test_upright_support_free_overhangs(shape, tmp_path):
    """No ledges/ceilings steeper than 45° from vertical above the build plate.

    A 0.5° allowance accounts for curved-surface tessellation, not intended
    unsupported horizontal faces. The only horizontal underside is at Z=0.
    This is a geometry criterion, not a guarantee for every filament/profile.
    """
    path = tmp_path / "overhang-audit.stl"
    assert shape.exportStl(str(path), tolerance=0.002, angularTolerance=0.05, relative=False)
    mesh = trimesh.load(path, force="mesh")
    on_plate = mesh.triangles[:, :, 2].max(axis=1) < 1e-5
    assert mesh.area_faces[on_plate].sum() > 400
    assert mesh.triangles[:, :, 2].min() >= -1e-5
    lower_normal_limit = -math.sin(math.radians(45.5))
    assert mesh.face_normals[~on_plate, 2].min() >= lower_normal_limit
