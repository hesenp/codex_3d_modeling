"""Fit diameters, attached labels, open bores, and slicer export validation."""

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

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fit_coupons", ROOT / "projects/04-fit-test-coupons/model.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


@pytest.fixture(scope="module")
def samples():
    return {(side, offset): require_solid(model.build(side, offset))
            for side in ("input", "output") for offset in model.OFFSETS_MM}


def test_fit_geometry_and_labels(samples):
    for (side, offset), shape in samples.items():
        outside = 57.15 - offset if side == "input" else 63.15 + offset
        inside = outside - 6
        info = inspect_shape(shape)
        assert info["size_mm"][2] == pytest.approx(50)
        assert info["min_mm"][2] == pytest.approx(0, abs=1e-6)
        # Section well clear of the lettering/lead-in must be an exact 3 mm annulus.
        section = shape.intersect(cq.Solid.makeCylinder(100, 1, (0, 0, 30)))
        assert section.Volume() == pytest.approx(np.pi * (outside**2 - inside**2) / 4)
        assert inspect_shape(section)["size_mm"][:2] == pytest.approx([outside, outside])
        bore = cq.Solid.makeCylinder(inside / 2 - 0.001, 52, (0, 0, -1))
        assert shape.intersect(bore).Volume() == pytest.approx(0, abs=1e-7)
        # Raised letters occupy only the upper tube wall, with flat, level front faces.
        raised = shape.cut(cq.Solid.makeCylinder(outside / 2 + 0.01, 51))
        assert raised.Volume() > 5
        assert inspect_shape(raised)["min_mm"][2] > 35
        assert inspect_shape(raised)["max_mm"][2] < 50
        lower = shape.intersect(cq.Solid.makeCylinder(100, 35))
        assert inspect_shape(lower)["size_mm"][:2] == pytest.approx([outside, outside])
        # Each glyph has a flat tangent front, but all characters share a level
        # baseline. This catches the previous arched cylindrical trimming.
        fronts = []
        for face in shape.Faces():
            if face.geomType() != "PLANE":
                continue
            normal, center = face.normalAt(), face.Center()
            tangent_distance = normal.x * center.x + normal.y * center.y
            if abs(normal.z) < 1e-6 and abs(tangent_distance - outside / 2 - 0.4) < 1e-6:
                fronts.append(face)
        assert len(fronts) == sum(len(line.replace(" ", "")) for line in model.labels(side, offset))
        if offset == 0:
            # The three zero digits in 0.00 must share their top/bottom heights.
            digit_faces = [face for face in fronts if 40 < face.Center().z < 44
                           and len(face.innerWires()) == 1]
            assert len(digit_faces) == 3
            bottoms = [inspect_shape(face)["min_mm"][2] for face in digit_faces]
            tops = [inspect_shape(face)["max_mm"][2] for face in digit_faces]
            assert max(bottoms) - min(bottoms) < 1e-6
            assert max(tops) - min(tops) < 1e-6


def test_sample_export_roundtrips(samples, tmp_path):
    for (side, offset), shape in samples.items():
        for path in export_model(shape, tmp_path, model.sample_name(side, offset)):
            if path.suffix == ".step":
                restored = require_solid(cq.importers.importStep(str(path)))
                assert restored.Volume() == pytest.approx(shape.Volume(), rel=1e-6)
                continue
            mesh = trimesh.load(path, force="mesh")
            assert mesh.is_watertight and mesh.is_winding_consistent
            assert len(mesh.split()) == 1
            assert mesh.volume == pytest.approx(shape.Volume(), rel=0.001)
            assert mesh.extents == pytest.approx(inspect_shape(shape)["size_mm"], abs=0.02)
            # Entry chamfers and diagonal glyph undersides stay within 45 degrees
            # of vertical; permit one degree of mesh approximation.
            floating_down = (mesh.face_normals[:, 2] < -np.sin(np.deg2rad(46))) & (mesh.triangles_center[:, 2] > 0.01)
            assert not floating_down.any()


def test_five_piece_plate_exports(samples, tmp_path):
    for side in ("input", "output"):
        plate = model.arrange_plate([samples[side, offset] for offset in model.OFFSETS_MM])
        info = inspect_shape(plate)
        assert info["valid"] and info["solids"] == 5
        assert all(length < 240 for length in info["size_mm"][:2])
        path = tmp_path / f"{side}-plate.3mf"
        cq.exporters.export(plate, str(path), unit="MM", tolerance=0.01, angularTolerance=0.1)
        mesh = trimesh.load(path, force="mesh")
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert len(mesh.split()) == 5
        assert mesh.extents == pytest.approx(info["size_mm"], abs=0.02)
        with ZipFile(path) as archive:
            xml_path = next(name for name in archive.namelist() if name.endswith(".model"))
            assert ET.fromstring(archive.read(xml_path)).attrib["unit"] == "millimeter"
