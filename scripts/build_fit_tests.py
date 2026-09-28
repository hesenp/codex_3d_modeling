#!/usr/bin/env python3
"""Export all ten labeled fit coupons and two upright five-piece 3MF plates."""

import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import cadquery as cq
from cadquery_helper.export import export_model, LINEAR_TOLERANCE_MM, ANGULAR_TOLERANCE_RAD
from cadquery_helper.models import inspect_shape, require_solid
from cadquery_helper.render import render_model


def main() -> None:
    project = ROOT / "projects/04-fit-test-coupons"
    spec = importlib.util.spec_from_file_location("fit_coupons", project / "model.py")
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    output = project / "output"
    report = {"offset_basis": "diameter", "nominal_diameter_mm": model.NOMINAL_DIAMETER_MM,
              "samples": [], "plates": {}}
    for side in ("input", "output"):
        samples = []
        for offset in model.OFFSETS_MM:
            shape = require_solid(model.build(side, offset))
            name = model.sample_name(side, offset)
            export_model(shape, output, name)
            outside, inside = model.dimensions(side, offset)
            report["samples"].append({"name": name, "side": side, "offset_mm": offset,
                                      "outside_diameter_mm": outside, "inside_diameter_mm": inside,
                                      "labels": model.labels(side, offset), **inspect_shape(shape)})
            samples.append(shape)
            print(f"Exported {name}", flush=True)
        plate = model.arrange_plate(samples)
        info = inspect_shape(plate)
        if not info["valid"] or info["solids"] != 5 or any(d > 256 for d in info["size_mm"]):
            raise ValueError(f"Invalid five-coupon P1S plate: {info}")
        cq.exporters.export(plate, str(output / f"{side}-plate.3mf"), unit="MM",
                            tolerance=LINEAR_TOLERANCE_MM, angularTolerance=ANGULAR_TOLERANCE_RAD)
        render_model(plate, output / f"{side}-plate.png", f"{side.title()} fit samples - diameter offsets 0 to 1 mm")
        render_model(samples[2], output / f"{side}-detail.png", f"{side.title()} - 0.50 mm diametral offset")
        report["plates"][side] = info
    (output / "inspection.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved ten samples and two plates to {output}")


if __name__ == "__main__":
    main()
