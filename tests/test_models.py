"""Check dimensional intent, the cavity, and the files delivered to a slicer."""

from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
import pytest
import trimesh

from cadquery_helper.export import export_model
from cadquery_helper.models import inspect_shape, load_model, require_solid

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module", params=["01-solid-block", "02-container"])
def project(request):
    return request.param, require_solid(load_model(ROOT / "projects" / request.param / "model.py"))


def test_geometry(project):
    name, shape = project
    info = inspect_shape(shape)
    expected = [10, 20, 30] if name == "01-solid-block" else [100, 100, 100]
    assert info["size_mm"] == pytest.approx(expected)
    assert info["min_mm"][2] == pytest.approx(0)
    solid = shape.Solids()[0]
    if name == "01-solid-block":
        assert info["volume_mm3"] == pytest.approx(6000)
        assert solid.isInside((0, 0, 15))
    else:
        assert not solid.isInside((0, 0, 50))
        assert not solid.isInside((0, 0, 100))
        assert solid.isInside((0, 0, 0.5))
        assert not solid.isInside((0, 0, 1.01))
        for x, y in [(49.5, 0), (-49.5, 0), (0, 49.5), (0, -49.5)]:
            assert solid.isInside((x, y, 50))
        for x, y in [(48.99, 0), (-48.99, 0), (0, 48.99), (0, -48.99)]:
            assert not solid.isInside((x, y, 50))
        # A 0.5 mm bevel removes the outside corner, leaving the 1 mm wall.
        assert not solid.isInside((49.9, 49.9, 50))
        assert solid.isInside((49.6, 49.6, 50))
        assert not solid.isInside((49.9, 0, 99.9))
        assert solid.isInside((49.6, 0, 99.6))
        assert not solid.isInside((49.9, 0, 0.1))
        assert solid.isInside((49.6, 0, 0.4))
        assert 48900 < info["volume_mm3"] < 49204


def test_export_roundtrip(project, tmp_path):
    name, shape = project
    paths = export_model(shape, tmp_path, name)
    info = inspect_shape(shape)
    for path in paths:
        assert path.stat().st_size > 0
        if path.suffix == ".step":
            restored = require_solid(cq.importers.importStep(str(path)))
            assert inspect_shape(restored)["size_mm"] == pytest.approx(info["size_mm"])
            assert restored.Volume() == pytest.approx(shape.Volume(), rel=1e-7)
            continue
        mesh = trimesh.load(str(path), force="mesh")
        assert mesh.is_watertight
        assert mesh.is_winding_consistent
        assert mesh.volume > 0
        assert len(mesh.split()) == 1
        assert np.allclose(mesh.extents, info["size_mm"], atol=1e-5)
        assert mesh.volume == pytest.approx(shape.Volume(), rel=1e-6)
        if path.suffix == ".3mf":
            with ZipFile(path) as archive:
                model_xml = next(item for item in archive.namelist() if item.endswith(".model"))
                xml = ET.fromstring(archive.read(model_xml))
                assert xml.attrib.get("unit", "millimeter") == "millimeter"
