"""Verify fit, indexing, threaded-guide clearance, and exported geometry."""

import importlib.util
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
import pytest
import trimesh

from cadquery_helper.export import export_model
from cadquery_helper.models import inspect_shape, require_solid

MODEL_PATH = Path(__file__).resolve().parents[1] / "projects/04-dowell-jig/model.py"


@pytest.fixture(scope="module")
def model():
    spec = importlib.util.spec_from_file_location("dowel_jig", MODEL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def shape(model):
    return require_solid(model.build())


def test_board_socket_and_registration_shoulder(shape, model):
    bounds = shape.BoundingBox()
    assert bounds.xlen == pytest.approx(model.OUTER_WIDTH_MM, abs=1e-6)
    assert bounds.ylen == pytest.approx(model.OUTER_THICKNESS_MM, abs=1e-6)
    assert bounds.zmin == pytest.approx(0, abs=1e-6)
    assert bounds.zmax == pytest.approx(model.TOTAL_HEIGHT_MM, abs=1e-6)

    inserted_board = cq.Workplane("XY", origin=(0, 0, model.ROOF_MM)).box(
        model.CAVITY_WIDTH_MM,
        model.CAVITY_THICKNESS_MM,
        model.SOCKET_DEPTH_MM + 1,
        centered=(True, True, False),
    ).val()
    assert shape.intersect(inserted_board).Volume() == pytest.approx(0, abs=1e-6)
    solid = shape.Solids()[0]
    # Probe the opposite half of the roof, clear of the offset guide opening.
    assert solid.isInside((6.35, 0, model.ROOF_MM - 0.5))
    assert not solid.isInside((6.35, 0, model.ROOF_MM + 0.5))


def test_flip_indexes_two_quarter_point_holes(model):
    centers = model.dowel_centers_from_left_edge()
    assert centers == pytest.approx((6.35, 19.05))
    assert centers[1] - centers[0] == pytest.approx(12.7)
    assert sum(centers) == pytest.approx(model.BOARD_WIDTH_MM)
    edge_material = centers[0] - model.DRILL_DIAMETER_MM / 2
    assert edge_material == pytest.approx(3.35)
    cross_grain_edge_material = (
        model.BOARD_THICKNESS_MM - model.DRILL_DIAMETER_MM
    ) / 2
    assert cross_grain_edge_material == pytest.approx(6.525)


def test_single_guide_avoids_impossible_two_guide_layout(model):
    centers = model.dowel_centers_from_left_edge()
    assert centers[1] - centers[0] < model.GUIDE_BODY_DIAMETER_MM
    assert 2 * model.GUIDE_BODY_DIAMETER_MM > model.BOARD_WIDTH_MM


def test_threaded_hole_clearance_and_helix(shape, model):
    axis = cq.Vector(model.GUIDE_X_MM, model.GUIDE_Y_MM, -0.1)
    minor_probe = cq.Solid.makeCylinder(
        model.THREAD_MINOR_DIAMETER_MM / 2,
        model.ROOF_MM + 0.2,
        axis,
    )
    assert shape.intersect(minor_probe).Volume() == pytest.approx(0, abs=1e-6)
    assert model.THREAD_MAJOR_DIAMETER_MM == pytest.approx(14.45)
    assert model.THREAD_MINOR_DIAMETER_MM == pytest.approx(13.367468)

    groove = model._thread_groove()
    groove_bounds = groove.BoundingBox()
    assert groove.isValid() and len(groove.Solids()) == 1
    assert groove_bounds.zlen > model.ROOF_MM
    assert groove.Volume() > 10


def test_dowel_jig_exports(shape, tmp_path):
    before = inspect_shape(shape)
    for path in export_model(shape, tmp_path, "dowel-jig"):
        if path.suffix == ".step":
            restored = require_solid(cq.importers.importStep(str(path)))
            assert restored.Volume() == pytest.approx(shape.Volume(), rel=1e-6)
            continue
        mesh = trimesh.load(str(path), force="mesh")
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert len(mesh.split()) == 1
        assert mesh.volume == pytest.approx(shape.Volume(), rel=0.003)
        assert np.allclose(mesh.extents, before["size_mm"], atol=0.03)
        if path.suffix == ".3mf":
            with ZipFile(path) as archive:
                xml_path = next(name for name in archive.namelist() if name.endswith(".model"))
                assert ET.fromstring(archive.read(xml_path)).attrib["unit"] == "millimeter"
