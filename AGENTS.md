# Working in this repository

This is a Python 3.12 / CadQuery workspace. Use pip, `.venv`, and
`requirements.txt`; keep dependencies and tooling local to the repository.

## CadQuery work

Use **$cadquery-helper** for creating, changing, exporting, or visually reviewing
models. Read [.agents/skills/cadquery-helper/SKILL.md](.agents/skills/cadquery-helper/SKILL.md)
if the skill is not already loaded. It is installed only in this repository.

- Name project folders `<number>-<project-title>` (for example `01-solid-block`).
  Put each independent design in `projects/<name>/model.py`, exposing `build()`
  that returns a CadQuery Workplane or Shape without writing files at import time.
- Use millimetres internally. Name dimensional parameters with `_MM`, document
  the requested units, and distinguish outside dimensions from cavity dimensions.
- Put reusable Python code in `src/cadquery_helper/` and command-line entry points
  in `scripts/`. Generated deliverables go in `projects/<name>/output/`.
- Follow code → build/export → render → visually inspect → update. Inspect actual
  CAD-derived PNGs and use numerical checks for dimensions and topology; an image
  alone cannot verify wall thickness or watertightness.

## Python workflow

Run from the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py all
XDG_CACHE_HOME="$PWD/.cache" .venv/bin/python -m pytest -q
```

The requirements file pins the complete tested environment and installs `src/`
in editable mode. Use `.venv/bin/python` explicitly when activation is uncertain.
When intentionally updating dependencies, refresh pins, verify `pip check`, run
the model checks, and update the skill's version guidance if CadQuery changes.
Keep parameter names clear and helpers small. Test geometric intent and export
round trips when changing geometry or exporters; documentation-only edits do not
need model tests.

## Git workflow

Inspect `git status --short --branch` and relevant diffs before editing. Preserve
unrelated user work. Review changes and stage explicit paths when a commit is
requested. Keep `.venv`, caches, secrets, and generated output out of Git. Source
models and instructions are the reproducible record. Commit, push, or rewrite
history only within the user's requested scope. Report generated artifact paths,
validation results, assumptions, and any outstanding limitations.
