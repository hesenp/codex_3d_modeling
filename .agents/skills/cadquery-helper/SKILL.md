---
name: cadquery-helper
description: Build, edit, export, and visually inspect parametric CadQuery models in this repository using its installed Python environment and shared rendering utilities. Use for CAD geometry and STL, 3MF, or STEP deliverables.
---

# CadQuery helper

This repo-local skill targets **CadQuery 2.8.0**, **cadquery-ocp 7.9.3.1.1**, and
**Python 3.12**, pinned in `requirements.txt`. Commands below run at the repository
root with `.venv/bin/python`. Set up a missing environment with
`python3.12 -m venv .venv` and `.venv/bin/python -m pip install -r requirements.txt`.
The editable install makes `src/cadquery_helper` available to project scripts.

## Model → render → inspect → update

1. Translate requested dimensions to millimetres. Establish outer versus inner
   size, wall/base thickness, open versus closed faces, and chamfer/fillet size.
   Clarify material ambiguity, or document a reasonable assumption when safe.
2. Name folders `<number>-<project-title>`, such as `01-solid-block`. Write
   `projects/<name>/model.py` with named `_MM` parameters and a `build()`
   returning a `cq.Workplane` or `cq.Shape`. Keep import/build free of output
   side effects. Existing examples are `01-solid-block` and `02-container`.
3. Build and export using the shared utility:

   ```bash
   .venv/bin/python scripts/build.py <name>
   ```

   This requires one valid positive-volume solid and writes STL, 3MF, STEP,
   `preview.png`, and `inspection.json` into the project's ignored `output/`.
   The build utility discovers all `projects/*/model.py`; `all` builds every one.
4. **Open and inspect the generated PNG** with an available image viewer. For
   Codex, use the image inspection tool on its absolute path. Check silhouettes,
   holes, opening, proportions, and details. Do not infer visual success solely
   from a successful script. If no image viewer is available, report that limit.
5. Reveal hollow parts with the reusable cutaway renderer:

   ```bash
   .venv/bin/python scripts/render.py projects/02-container/model.py \
     --output projects/02-container/output/cutaway.png --cutaway
   ```

   It can also render `.step`/`.stp`. Cutaway keeps Y >= the bounding-box midpoint
   for inspection only; it does not modify the model or exported files. Previews
   use VTK's offscreen EGL renderer and actual tessellated CAD geometry. A depth
   buffer correctly handles thin walls that painter-sorted triangles can
   misrender. Isometric, top, and front views preserve equal axis scaling.
6. Fix geometry or viewing issues supported by the inspection, rebuild, and
   inspect again. Use exact CAD measurements and mesh checks alongside images:

   ```bash
   XDG_CACHE_HOME="$PWD/.cache" .venv/bin/python -m pytest -q
   .venv/bin/python -m pip check
   ```

   Extend checks for new design intent when warranted: bounds, volume, solid
   count, cavities and walls, mesh watertightness/winding, and exported units.
   Deliver the artifact paths, confirmed dimensions, and verification results.

## APIs verified against the installed version

```python
import cadquery as cq
from cadquery_helper.models import inspect_shape, require_solid

result = cq.Workplane("XY").box(10, 20, 30, centered=(True, True, False))
shape = require_solid(result)
print(inspect_shape(shape))
```

- `box` centers all axes by default; `(True, True, False)` places the bottom at
  Z = 0. Select faces/edges intentionally before `shell`, `chamfer`, or `fillet`.
- For the example container, chamfer the exterior box **before** subtracting the
  cavity to leave the interior edges sharp. Chamfers remove material locally;
  flat-wall thickness does not imply constant thickness at beveled edges.
  Avoid chamfers consuming the entire thin wall or base.
- `shape.isValid()`, `shape.Solids()`, `shape.Volume()`, and `shape.BoundingBox()`
  provide exact CAD checks. A hollow open-top container is still one solid: its
  material boundary must be closed even though its cavity is open.
- Prefer `cadquery_helper.export.export_model` for one solid. It uses
  `shape.exportStl(..., tolerance=0.01, angularTolerance=0.1, relative=False)`
  and `cq.exporters.export(shape, path, tolerance=0.01,
  angularTolerance=0.1, unit="MM")` for 3MF/STEP.
  Linear deflection is in mm; angular deflection is in radians. STL is unitless,
  so tell consumers to import it as mm. 3MF stores units; these are geometry
  exports without slicer presets. Keep Python source for parametric editing.
- `shape.tessellate(tolerance, angularTolerance)` returns vectors and triangle
  index triples. The shared renderer uses this API without a GUI/display server
  on this Linux host; EGL support is required (Mesa software rendering works).
- The current build/export utility intentionally handles a single solid. For
  multi-part requests, add an explicit assembly workflow and part-count checks.

Verify `.venv/bin/python -c 'import cadquery; print(cadquery.__version__)'` when
debugging API differences. After an intentional upgrade, update pins and this
skill together, rebuild example projects, inspect previews, and rerun validation.
Consult [CadQuery's export reference](https://cadquery.readthedocs.io/en/latest/importexport.html)
for additional formats, verifying signatures against the installed package.
