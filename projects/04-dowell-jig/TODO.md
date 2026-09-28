# 6 mm dowel jig

- [x] Fit the actual 1 × 0.75 inch (25.4 × 19.05 mm) board end.
- [x] Put two 6 mm dowel centers on the thickness centerline.
- [x] Check the guide collision: two 16 mm guide bodies cannot fit at the desired
  12.7 mm quarter-point spacing.
- [x] Use one guide at a 6.35 mm offset and flip the jig 180° to index the second
  symmetric hole.
- [x] Model the pictured M14×1 female thread with 0.45 mm diametral FDM clearance.
- [x] Match the 10 mm threaded guide length with a 10 mm jig roof.
- [x] Add numerical geometry and export checks.
- [ ] Print a thread coupon and tune `THREAD_DIAMETRAL_CLEARANCE_MM` for the
  specific printer/material before printing the full jig.
- [ ] Measure the real board and tune `BOARD_WIDTH_CLEARANCE_MM` and
  `BOARD_THICKNESS_CLEARANCE_MM` if needed.
