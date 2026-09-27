# CadQuery modeling workspace

Python 3.12, pip, and CadQuery **2.8.0**. Every model uses **millimetres** internally.

## Setup and build

The local `.venv` is already installed. To recreate it on a compatible Linux host:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py all
XDG_CACHE_HOME="$PWD/.cache" .venv/bin/python -m pytest -q
```

`requirements.txt` pins the tested dependencies and installs the shared package
in editable mode. `pyproject.toml` only provides Python packaging and pytest
configuration; pip and requirements.txt manage the environment.

```text
.agents/skills/cadquery-helper/   Repository-local Codex skill
projects/01-solid-block/model.py    10 × 20 × 30 mm solid
projects/02-container/model.py      100 mm open-top container
projects/03-y-manifold/model.py     Curved dust-collection Y-manifold
projects/*/output/               Generated STL, 3MF, STEP, PNG, and JSON
src/cadquery_helper/             Shared export, inspection, and rendering code
scripts/                        Build and rendering entry points
tests/                          Geometry and exported-file validation
```

## Example projects

| Project | Geometry | Output |
| --- | --- | --- |
| [Solid block](projects/01-solid-block/model.py) | 1 × 2 × 3 cm = 10 × 20 × 30 mm; 6,000 mm³ | [STL](projects/01-solid-block/output/01-solid-block.stl), [3MF](projects/01-solid-block/output/01-solid-block.3mf), [preview](projects/01-solid-block/output/preview.png) |
| [Container](projects/02-container/model.py) | 10 × 10 × 10 cm outside; open top; 1 mm walls/base; 0.5 mm exterior chamfers | [STL](projects/02-container/output/02-container.stl), [3MF](projects/02-container/output/02-container.3mf), [preview](projects/02-container/output/preview.png) |
| [Y-manifold](projects/03-y-manifold/README.md) | Two 56.65 mm OD male inlets; 57.65 mm ID female outlet; 90° side inlet curving to a 45° junction; 3 mm walls | [STL](projects/03-y-manifold/output/03-y-manifold.stl), [3MF](projects/03-y-manifold/output/03-y-manifold.3mf), [preview](projects/03-y-manifold/output/preview.png) |

The container dimensions and chamfer size were confirmed during setup. The
cavity is 98 × 98 × 99 mm. Walls and base are 1 mm on their flat regions;
exterior chamfers locally reduce thickness at the edges, leaving a 0.5 mm top
rim on the straight sides. The inner rim and cavity corners are sharp. There is
no lid. The block and container sit at Z = 0 and are centered in X/Y.

All builds also emit an editable-geometry STEP file and `inspection.json` with
exact bounds, volume, solid count, and CAD validity. STL has no stored units;
import it as millimetres. The 3MF export records millimetres explicitly and
contains geometry, without printer or slicer settings.

## Edit → render → inspect → update

Change a project's named parameters, rebuild it, and inspect the new PNG:

```bash
.venv/bin/python scripts/build.py 02-container
.venv/bin/python scripts/render.py projects/02-container/model.py \
  --output projects/02-container/output/cutaway.png \
  --title 'Container · 1 mm walls and base' --cutaway
```

The renderer uses VTK's offscreen EGL backend and CAD tessellation, with a depth
buffer to correctly display thin walls. It needs no display server on this
Linux host (Mesa software rendering is supported); other hosts need a working
EGL implementation. It supports `.py` files exposing `build()` and STEP
files. Only run Python model files you trust, since loading executes Python.
Cutaway previews expose the rear half at mid-Y and do not change exported parts.
Open the PNG with an image viewer or Codex's image inspection tool, check the
shape and opening, then adjust and repeat as necessary.

The tests validate dimensions, volume, cavity, wall/base thickness at probe
points, chamfer locations, connected watertight STL/3MF meshes with consistent
winding, 3MF units, and STEP round trips. Generated artifacts are ignored by Git
and recreated with the commands above; source models remain the source of truth.

## Codex skill

Use `$cadquery-helper` in this repository. Its
[SKILL.md](.agents/skills/cadquery-helper/SKILL.md) documents the installed API,
export tolerances, and visual review workflow. The shared build/render tools
serve as its utilities. Repo-local discovery follows the
[official Codex skill documentation](https://learn.chatgpt.com/docs/build-skills).
If the new skill does not appear in an existing session, restart Codex in this
folder; `AGENTS.md` also points to it directly.

CadQuery references: [installation](https://cadquery.readthedocs.io/en/latest/installation.html)
and [export formats](https://cadquery.readthedocs.io/en/latest/importexport.html).
The installed 2.8.0 API and the local tests govern this workspace if upstream
documentation moves to a newer version.
