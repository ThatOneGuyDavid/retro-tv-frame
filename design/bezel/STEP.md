# Editable green bezel — STEP

- [Full bezel](bezel-assembled.step): one continuous solid in the installed coordinate system; glass is Z0, inner underside land is Z1.
- [Left print half](bezel-left.step) and [right print half](bezel-right.step): individual solids translated to the same nominal XY / Z0 print datum as their STLs.
- [Joining key](joining-key.step): print two per complete bezel.

Units are millimeters. Import the full bezel to adapt the design to a different display. Use the halves when editing individual printable pieces. These are curved boundary-representation (B-rep) solids, with spline surfaces and planar fitting features, rather than thousands of triangle faces wrapped in STEP.

STEP carries editable solid geometry, but does not preserve a native CAD feature tree or driving dimensions. For repeatable dimensional changes, edit [build_step.py](build_step.py), which reconstructs the v8 equations, flange, twelve feet, eight locating tabs, seam pockets and flat underside land. Measurements and feature stations must be adjusted together for another display.

The STEP surfaces are a smooth reconstruction of the sampled v8 mesh geometry, not a bit-for-bit conversion. See [STEP verification](step-validation.json) for round-trip solid validity, volume, bounds and deterministic bidirectional sampled surface comparisons. Sampling does not prove a maximum deviation everywhere. The verified sampled difference is below 0.15 mm (12,000 surface points in each direction per part); the reconstructed splines can extend about 0.15 mm beyond nominal XY bounds. Original STLs remain unchanged and are the existing print reference. The assembly's existing interference checks cover those STLs, not a new physical fit of edited STEP geometry.

## Regenerate and verify

Use a separate virtual environment with Python 3.14:

```bash
python -m venv .venv-step
source .venv-step/bin/activate
pip install -r requirements-step.txt
python build_step.py
python verify_step.py
```

Run from this directory. The builder writes four STEP files and round-trip validation; the verifier adds comparison evidence against the adjacent STLs. Both run locally. No STL files are overwritten. CAD edits still need fitting samples before full printing or bonding.
