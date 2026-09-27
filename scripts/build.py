#!/usr/bin/env python3
"""Build one or all project models, export files, and render previews."""

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))

from cadquery_helper.export import export_model
from cadquery_helper.models import inspect_shape, load_model, require_solid
from cadquery_helper.render import render_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default="all", help="Project folder name, or all")
    args = parser.parse_args()
    projects = {path.parent.name: path for path in sorted((ROOT / "projects").glob("*/model.py"))}
    if args.project != "all" and args.project not in projects:
        parser.error(f"Unknown project {args.project!r}; choose from {', '.join(projects)}")
    for name, path in projects.items():
        if args.project not in ("all", name):
            continue
        shape = require_solid(load_model(path))
        output = path.parent / "output"
        paths = export_model(shape, output, name)
        paths.append(render_model(shape, output / "preview.png", name.replace("-", " ").title()))
        report = output / "inspection.json"
        report.write_text(json.dumps(inspect_shape(shape), indent=2) + "\n")
        paths.append(report)
        print(f"{name}:")
        for artifact in paths:
            print(f"  {artifact.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
