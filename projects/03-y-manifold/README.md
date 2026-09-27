# Smooth 45° dust-collection Y-manifold

Input 1 and the outlet are coaxial. Input 2 is a straight tube at **45°** to
input 1, joining toward the outlet. The manifold uses the user-confirmed
**0.5 mm clearance on diameter**, not per side; nominal 2¼ inches is 57.15 mm.

| Port | Connection | Mating dimension | Bore | Straight engagement |
| --- | --- | --- | --- | --- |
| Input 1, upper end | Male, to saw-base connection | **56.65 mm OD** | 50.65 mm | 35 mm |
| Input 2, 45° branch | Male, to guard dust-collection connection | **56.65 mm OD** | 50.65 mm | 35 mm |
| Outlet, lower end | Female, to shop-vac connection | **57.65 mm ID** | 57.65 mm | 35 mm |

## Dimensions and printer fit

- Overall bounds: approximately **132.64 × 63.65 × 240 mm** (X × Y × Z).
- Input 1 mouth to Y centerline junction: **150 mm**, shortened by **15.8 mm**.
- Outlet mouth to Y centerline junction: **90 mm**.
- Input 2 centerline junction-to-mouth length: **115 mm**, with no bend.
- Input 2 mouth center: **X = 81.32 mm, Y = 0, Z = 171.32 mm**.
- Connection wall thickness: **3 mm**, giving an outlet OD of 63.65 mm.
  Smooth reinforcement increases the main-body wall to **4.675 mm** and the
  branch-body wall to **4.175 mm**, tapering back to the connection dimensions.
- Each port has at least 35 mm of unobstructed cylindrical mating surface plus
  a **0.75 mm × 45° insertion bevel**, which reduces thickness locally.
- Outlet socket length including bevel: **35.75 mm**, followed by a **20 mm
  conical transition** to the main bore. Wall thickness on the cone is 3 mm
  radially (slightly less perpendicular to the cone surface).

The [Bambu Lab P1S specifications](https://us.store.bambulab.com/collections/3d-printer/products/p1s)
list a 256 × 256 × 256 mm build volume. The 240 mm design height leaves 16 mm
below that nominal limit and also stays below 250 mm. The model sits at Z = 0,
with the outlet down and input 1 up. Center it on the plate in Bambu Studio;
the centered footprint has ample lateral room for an optional adhesion brim. Fit has
been checked geometrically, not by running a printer-specific slicing profile.

The model is one hollow solid. The smooth exterior volumes are fused first, then
the joined bores are subtracted together so the trunk wall cannot block the
branch. No thread, hose barb, clamp groove, or proprietary coupling is assumed.
Fit to the actual saw, guard hose, and vacuum hardware has not been physically
tested; no airflow simulation or physical dust-extraction test was performed.
Edit the named millimetre parameters in [model.py](model.py) to change dimensions.

## Smooth exterior and support-free orientation

The fluid, Model Y-inspired treatment replaces projecting ribs and angular
panels with distributed wall thickening, smooth neck transitions, and a **3 mm
junction blend**. The round connections and 45° straight branch remain intact.
The main body and branch use tangent-continuous spline profiles revolved about
their axes. Their outside radii decrease toward the inlet mouths, avoiding
unsupported steps or reinforcing bands.

**Print upright with the outlet on the build plate, input 1 vertical, and
supports disabled.** Keep the exported orientation; rotating the part changes
the overhang result. Center it on the P1S plate. An optional brim is for bed
adhesion, not support underneath the model. Use your calibrated filament profile
and inspect the sliced layer preview before printing.

The geometry check evaluates the complete surface, including inside the bores.
It excludes only the bed-contact faces at Z=0 and requires all other downward
surfaces to stay within **45° of vertical**, allowing **0.5°** for tessellation
error. It also checks that the model touches the plate and does not extend below
it. There are no internal ledges intended to require trapped support material.
The audit is a geometric design check, not a physical print test or a completed
Bambu Studio slice; filament, cooling, and layer settings still affect quality.

All three 35 mm connection lengths and insertion bevels stay clear. The added
body thickness is intended as reinforcement; it has not been load-tested.

## Deliverables

- [STL](output/03-y-manifold.stl) — import as millimetres.
- [3MF](output/03-y-manifold.3mf) — stored millimetres; geometry only, not sliced.
- [STEP](output/03-y-manifold.step) — exact CAD geometry.
- [Exterior preview](output/preview.png) and [cutaway](output/cutaway.png).
- [Geometry report](output/inspection.json) and [export overhang audit](output/printability.json).

The full model is the printable deliverable; the cutaway is for inspection only.
From the repository root:

```bash
.venv/bin/python scripts/build.py 03-y-manifold
.venv/bin/python scripts/render.py projects/03-y-manifold/model.py \
  --output projects/03-y-manifold/output/cutaway.png \
  --title 'Smooth Y-manifold - print upright, outlet down' --cutaway
XDG_CACHE_HOME="$PWD/.cache" .venv/bin/python -m pytest -q
```

Validation measures actual circular sections for all three fits, checks the 45°
layout, connection walls and bevels, and probes the full straight bores for
obstructions. The printer-envelope check verifies dimensions and clearance.
STL/3MF tests verify a single connected watertight mesh, consistent winding,
scale, and volume agreement with CAD; STEP is checked after reimport.
Reinforcement checks verify added body material and clear mating lengths and
bores. The overhang regression test evaluates a fine mesh in the specified
upright orientation. Exterior and cutaway previews were visually inspected.
