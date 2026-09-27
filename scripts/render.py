#!/usr/bin/env python3
"""Render a trusted local model.py or STEP model to a PNG review sheet."""

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))

import cadquery as cq

from cadquery_helper.models import load_model
from cadquery_helper.render import render_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", default="CadQuery model")
    parser.add_argument("--cutaway", action="store_true", help="Expose the section at mid-Y")
    args = parser.parse_args()
    if args.model.suffix.lower() in (".step", ".stp"):
        model = cq.importers.importStep(str(args.model))
    elif args.model.suffix.lower() == ".py":
        model = load_model(args.model)
    else:
        parser.error("Expected a .py, .step, or .stp model")
    print(render_model(model, args.output, args.title, args.cutaway))


if __name__ == "__main__":
    main()
