# Curved dust-collection Y-manifold

Built from [y-manifold.md](y-manifold.md). The user confirmed that the diameters
refer to the manifold itself, with **0.5 mm clearance on diameter**, not per side.
Nominal 2¼ inches is 57.15 mm. Input 2's mating connection is **90°** to input 1;
a circular bend eases it into a **45°** branch at the main-tube junction.
the inp
| Port | Connection | Mating dimension | Bore | Straight engagement |
| --- | --- | --- | --- | --- |
| Input 1, straight upper end | Male, to saw-base connection | **56.65 mm OD** | 50.65 mm | 35 mm |
| Input 2, horizontal side connection | Male, to guard dust-collection connection | **56.65 mm OD** | 50.65 mm | 35 mm |
| Outlet, lower end | Female, to shop-vac connection | **57.65 mm ID** | 57.65 mm | 35 mm |

The manifold is one hollow solid. Input 1 and the outlet share the Z axis;
input 2's straight mating cuff points along +X, perpendicular to that axis.
Moving inward from the cuff, the tube curves toward the outlet and joins the
main passage at 45° in the XZ plane. The bottom of the outlet is Z = 0.
The full model, not the cutaway, is
the printable deliverable.

## Chosen dimensions

- Nominal wall thickness: **3 mm**, giving an outlet OD of 63.65 mm.
- Input 1 mouth to Y centerline junction: **165.8 mm**, extended by **50.8 mm
  (2 inches)** from the previous design.
- Outlet mouth to Y centerline junction: **90 mm**, shortened by **15 mm**.
  The reduction is in the straight section above the outlet transition; the
  outlet's 35 mm connection length is retained.
- Main end-to-end length: **255.8 mm**. Overall bounds are approximately
  **164.45 × 63.65 × 255.8 mm** (X × Y × Z).
- Branch junction center: **90 mm** above the outlet end.
- Straight branch root from the junction: **72 mm** at 45° to the main axis.
- Bend centerline radius: **65 mm**, with a **45° circular arc** joining the
  root and horizontal cuff tangentially (no abrupt angle at either end).
- Branch centerline length from junction to mouth: approximately **158.80 mm**,
  including the 51.05 mm arc and 35.75 mm cuff plus bevel.
- Input 2 mouth center: approximately **X = 132.62 mm, Y = 0, Z = 159.95 mm**.
- Each port has 35 mm of unobstructed cylindrical mating surface plus a
  **0.75 mm × 45° insertion bevel**. The bevel reduces wall thickness locally.
- Outlet socket length including the bevel: 35.75 mm, followed by a **20 mm
  conical transition** to the 50.65 mm main bore. Wall thickness is 3 mm measured
  radially on the cone (slightly less measured perpendicular to its surface).
- No thread, hose barb, clamp groove, or proprietary coupling is assumed.

The inlet extension is user-requested; the 15 mm outlet reduction implements
“a bit shorter.” Other lengths and wall thickness are design choices because
the original specification supplied only port diameters and angles.
Edit the named parameters in [model.py](model.py)
to change them. The geometry uses the supplied connection dimensions; fit to the
actual saw, guard hose, and vacuum hardware has not been physically tested.

The branch exterior and bore are swept along the same line–arc–line centerline,
preserving the round 50.65 mm bore and 3 mm walls through the bend. The exterior
volumes are fused first, then the joined bores are subtracted together to avoid
a wall blocking the Y intersection. The final 45° junction with the trunk is a
direct tube intersection; the outlet transition is tapered.
No airflow simulation or physical dust-extraction test has been performed.

## Deliverables

- [STL](output/03-y-manifold.stl) — import as millimetres.
- [3MF](output/03-y-manifold.3mf) — millimetres stored in the file; geometry only.
- [STEP](output/03-y-manifold.step) — exact CAD geometry.
- [Exterior preview](output/preview.png) and [cutaway](output/cutaway.png).
- [Geometry report](output/inspection.json).

From the repository root:

```bash
.venv/bin/python scripts/build.py 03-y-manifold
.venv/bin/python scripts/render.py projects/03-y-manifold/model.py \
  --output projects/03-y-manifold/output/cutaway.png \
  --title 'Curved Y-manifold - internal passages' --cutaway
XDG_CACHE_HOME="$PWD/.cache" .venv/bin/python -m pytest -q
```

Validation measures actual circular cross-sections for all three fits, checks
the 90° mating axis, 45° junction, bend radius and tangent continuity, and
connection walls. Normal sections through the bend confirm its circular bore
and wall dimensions; full-bore cylinder and sphere probes detect obstructions.
Checks also verify the insertion bevels. STL and
3MF are checked for one connected watertight mesh, consistent winding, correct
scale, and volume agreement with the CAD solid; STEP is checked after reimport.
Both exterior and cutaway previews were visually inspected.
