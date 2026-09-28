# Flip-indexed 6 mm dowel jig

This is a one-piece printed end-cap jig for a board whose actual end section is
1 × 0.75 inch (25.4 × 19.05 mm). It accepts one metal M14×1 drill guide with a
6 mm bore and 10 mm threaded length.

The guide is 6.35 mm from one edge of the board. Drill the first hole, remove
the jig, rotate it 180° around the drilling axis, reseat it fully against the
board end, and drill the second hole. The resulting centers are 6.35 and
19.05 mm from the same long-edge endpoint, both centered across the 19.05 mm
board thickness.

## Why the jig flips

The desired quarter-point spacing is 12.7 mm, but each guide body is 16 mm in
diameter. Two guides would overlap by 3.3 mm. Even placing them tangent would
move the 6 mm dowel holes close to the board edges. Reusing one guide by flipping
the cap keeps 3.35 mm of wood between each hole and its nearest width edge and
6.525 mm to either thickness edge.

## Fit assumptions

- The board cavity adds 0.6 mm across the 25.4 mm width and 0.5 mm across the
  19.05 mm thickness. Measure the real board and tune these two constants before
  printing if its size or printer calibration differs.
- The female M14×1 thread adds 0.45 mm diametral FDM clearance. Print a short
  thread coupon first if a snug or loose fit would be costly.
- The 10 mm roof matches the pictured 10 mm threaded length, so the metal guide
  tip ends flush with the board-registration surface when its shoulder is seated.
- The guide dimensions come from `guide.png`: M14×1, 6 mm bore, 10 mm threaded
  length, 16 mm body diameter, and 30 mm overall length.

Build from the repository root:

```bash
.venv/bin/python scripts/build.py 04-dowell-jig
```

Generated STL, 3MF, STEP, preview, and inspection files are written to
`projects/04-dowell-jig/output/`. Import the STL as millimetres; the 3MF and STEP
files retain units.
