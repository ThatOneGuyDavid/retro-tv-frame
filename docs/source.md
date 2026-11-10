# Source, rebuilding and checks

## One current snapshot

The repository contains the current design and its editable source. `design/bezel/` contains **bezel v8** (stable filenames), including the permanent flat inner printing land. The build scripts generate the parts directly from dimensional geometry. They use Python numerical mesh construction and Manifold boolean operations through trimesh, with matplotlib for diagrams and full-scale paper artwork.

| Builder | Main responsibility |
| --- | --- |
| `design/display/build.py` | Measured generic display envelope and Z datum |
| `design/knobs/build.py` | Five knob pieces, fit clearances and assembly |
| `design/grille/build.py` | Perforations, top/bottom mounting bands, sample |
| `design/bezel/build.py` | Curve, lips, flange, joints, feet, locators, samples |
| `design/assembly/build.py` | Positions, wood/rails/grooves, pair checks, viewer, cut list |
| `design/faceplate/build.py` | Clean woodworking SVG/PDF and registration marks |

The files are coordinated example geometry, not a universal resizer. Glass half-width/height, post and locator stations, joint positions, assembly column positions, outline/cutout dimensions, and template labels all need attention during adaptation. Some assertions encode example-specific targets; update them to test the new design rather than removing them to hide a failure.

## Build

The supplied top-level `requirements.txt` pins the main package versions used with Python 3.14. Create a virtual environment, install them, and run:

```bash
python tools/build.py
python tools/verify.py
```

If Node.js is available, `node tools/check-viewer.cjs` exercises the actual viewer's tree membership, grouped visibility, sibling isolation, and mixed checkbox states. It also checks the zoom slider/readout, mouse-wheel limits and synchronization, and Fit reset. These are control-logic checks with a minimal DOM, not a claim of WebGL/browser rendering coverage.

Build order is display → knobs → grille → bezel → assembly → clean faceplate. A display reference is included so individual builders can be inspected, but the full build starts from source. The assembly builder also writes its own consistent one-piece display reference. The clean template reads the assembly's verified wood bounds.

All output is local. There are no model/API requests, private paths, device identities, or cloud dependencies in the builders. The offline WebGL viewer embeds the actual triangles and needs no external JavaScript library. The public diagrams show CAD geometry; none is labeled as a build photograph.

The glass test card is procedural fragment-shader artwork attached to the display's local viewing coordinates, with a UI toggle. It does not alter the display mesh, STL files, or GLB materials. The static front diagram includes a clipped color-bar illustration. It is decorative, not a calibrated test signal.

The clean faceplate PDF/SVG is the preferred cutting artifact. The assembly builder also emits an annotated technical template; it is useful for fit review but is not the simplified woodworking printout linked by the README.

## What verification covers

- Watertight, positive-volume geometry and connected surfaces for printed parts.
- Reimported bezel STLs after float32 serialization cleanup.
- Inner-lip underside at Z1, locator tips at Z3 and the intended fitting clearances.
- Glue-foot footprints on the modeled factory frame and nominal Z7.2 contact plane.
- Joint/key clearance from the inner opening and measured display.
- All **210 static part-pair checks** across the full **21-component** assembly, using separated bounding boxes or solid-intersection volumes as appropriate.
- Source-mesh fingerprints, including the current v8 bezel used by the frame model.
- True-scale Letter page setup and full tile coverage. The clean template contains three closed cut contours and no other-layer outlines.
- Local links, file inventory, and checksums in the prepared package.

`validation.json` files live with their builders. They are machine-check evidence, not proof of physical strength or a record of completed construction. Numerical fit depends on the reference envelope; actual printers, adhesive, material thickness, finish buildup, stands, speaker acoustics and ventilation need workshop checks. The repository does not claim a finished electronics integration or measured structural load capacity.

## Physical test status

The bezel v8 test print was reported successful on **2026-11-10**. This is a reported physical result, separate from the numerical checks and the earlier slice evidence in `design/bezel/first-layer-check.json`. That JSON remains a record of its diagnostic slice, not a record of the later physical test. The exact successful print settings have not been recorded. Display fit, adhesive joints, woodworking and final assembly remain to be checked.

## Contributing an adaptation

Share the measurements needed to reproduce the geometry, anonymous if preferred. Include a clear front/section view, fitting sample results, exact part files, and a description of any unmodeled features. Do not call an adaptation universal merely because it scales visually. Keep current build instructions synchronized with geometry and actual hardware decisions.
