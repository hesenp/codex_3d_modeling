"""Verify mating sizes, a 90° inlet curving to 45°, open bores, and exports."""

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
        (cq.Vector(0, 0, model.MAIN_LENGTH_MM - 20), cq.Vector(0, 0, 1), [50.65, 56.65]),
        (model.INLET_2_MOUTH - model.INLET_2_AXIS * 15, model.INLET_2_AXIS, [50.65, 56.65]),
        (cq.Vector(0, 0, 15), cq.Vector(0, 0, 1), [57.65, 63.65]),
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
    assert math.degrees(math.acos(model.BRANCH_ROOT_AXIS.dot(model.Z_AXIS))) == pytest.approx(45)
    assert math.degrees(math.acos(model.INLET_2_AXIS.dot(model.Z_AXIS))) == pytest.approx(90)
    bounds = shape.BoundingBox()
    assert bounds.zmin == pytest.approx(0, abs=1e-6)
    assert bounds.zmax == pytest.approx(255.8, abs=1e-6)
    assert model.JUNCTION.z - bounds.zmin == pytest.approx(90.0, abs=1e-6)
    assert bounds.zmax - model.JUNCTION.z == pytest.approx(115.0 + 50.8, abs=1e-6)
    assert bounds.ylen == pytest.approx(63.65, abs=1e-6)
    solid = shape.Solids()[0]
    # Probe each full bore with an independent cylinder to catch leftover septa.
    probes = [
        cq.Solid.makeCylinder(25.2, model.MAIN_LENGTH_MM + 2, (0, 0, -1)),
        cq.Solid.makeCylinder(25.2, model.BRANCH_ROOT_LENGTH_MM,
                             model.JUNCTION, model.BRANCH_ROOT_AXIS),
        cq.Solid.makeCylinder(25.2, 37, model.BEND_END, model.INLET_2_AXIS),
        cq.Solid.makeCylinder(28.7, 34, (0, 0, 1)),
    ]
    for probe in probes:
        assert shape.intersect(probe).Volume() == pytest.approx(0, abs=1e-6)
    passage = model.flow_passage()
    assert passage.isValid() and len(passage.Solids()) == 1
    # Model contains exactly the exterior minus the connected passage.
    assert shape.Volume() == pytest.approx(
        model.outer_envelope().Volume()
        - model.outer_envelope().intersect(passage).Volume(), rel=1e-7
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
    assert not solid.isInside((28.2, 0, model.MAIN_LENGTH_MM - 0.1))
    assert solid.isInside((28.2, 0, model.MAIN_LENGTH_MM - 1.0))
    assert not solid.isInside((29.4, 0, 0.1))
    assert solid.isInside((29.4, 0, 1.0))
    for distance, inside in [(0.1, False), (1.0, True)]:
        point = model.INLET_2_MOUTH - model.INLET_2_AXIS * distance + cq.Vector(0, 28.2, 0)
        assert solid.isInside(point) == inside


def test_bend_geometry_and_clearance(shape, model):
    path = model.branch_path()
    arcs = [edge for edge in path.Edges() if edge.geomType() == "CIRCLE"]
    assert len(arcs) == 1
    arc = arcs[0]
    assert arc.radius() == pytest.approx(65)
    assert arc.Length() / arc.radius() == pytest.approx(math.pi / 4)
    assert arc.tangentAt(0).dot(model.BRANCH_ROOT_AXIS) == pytest.approx(1)
    assert arc.tangentAt(1).dot(model.INLET_2_AXIS) == pytest.approx(1)

    # Inspect normal sections through the actual solid at several bend angles.
    # Full-bore spheres independently check for plugs inside the curved passage.
    for angle in (50, 60, 75, 85):
        center = model.bend_point(angle)
        normal = cq.Vector(math.sin(math.radians(angle)), 0, math.cos(math.radians(angle)))
        section = cq.Workplane(cq.Plane(origin=center, normal=normal)).newObject([shape]).section()
        diameters = sorted(2 * edge.radius() for edge in section.edges().vals()
                           if edge.geomType() == "CIRCLE"
                           and (edge.arcCenter() - center).Length < 1e-5)
        assert diameters == pytest.approx([50.65, 56.65], abs=1e-5)
        probe = cq.Solid.makeSphere(25.2, center, angleDegrees1=-90, angleDegrees2=90)
        assert shape.intersect(probe).Volume() == pytest.approx(0, abs=1e-6)


def test_manifold_exports(shape, tmp_path):
    before = inspect_shape(shape)
    expected_bounds = before["size_mm"]
    for path in export_model(shape, tmp_path, "y-manifold"):
        if path.suffix == ".step":
            restored = require_solid(cq.importers.importStep(str(path)))
            assert restored.Volume() == pytest.approx(shape.Volume(), rel=1e-6)
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
