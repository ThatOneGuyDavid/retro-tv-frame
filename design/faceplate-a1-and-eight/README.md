# Faceplate patterns

Both patterns use the current assembly faceplate geometry: an 816.2 × 434.75 mm outer edge, a curved 640 × 369 mm screen opening, and a 100 × 160 mm speaker opening with 8 mm corners. The PDF has reference crosses for the two planned knob centers; no shaft holes are specified because hardware has not been chosen. View is from the front, top up.

## One-sheet paper pattern

[Download A1 landscape PDF](faceplate-cutouts-a1-one-sheet.pdf) (841 × 594 mm). It shows the **full outer faceplate edge and both inner cutouts**, so the paper can be aligned to the workpiece. The 100 mm bar and 25.4 mm square are inside the screen void. The two labeled crosses are knob-center references at x=392.5 mm, y=130 and 40 mm in the assembly datum; they are not cut lines. Print at **Actual Size / 100%**, with Fit, Shrink, and Scale to printable area disabled. Measure both scale checks before transferring cut lines. The first Letter print scaled incorrectly, so do not skip this check.

## 3D printed pattern

The faceplate is split along its narrow material bands into eight sections: [left top](left-top.stl), [left bottom](left-bottom.stl), [screen top left](top-left.stl), [screen top right](top-right.stl), [screen bottom left](bottom-left.stl), [screen bottom right](bottom-right.stl), [control-side top](controls-top.stl), and [control/speaker](controls-speaker.stl). These are **full-area faceplate sections**, including the outer perimeter and actual openings, not thin tracing frames. Each is 3.175 mm thick to match the nominal 1/8 inch faceplate.

For the prepared two-build-plate arrangement, import [plate 1: outer sections](plate-1-outer-sections.stl) and [plate 2: screen edges](plate-2-screen-edges.stl) separately. Each plate STL contains four unconnected parts in verified, non-overlapping 420 × 420 mm positions. [View the plate layout](two-plate-layout.png). Plate 2 has at least 7 mm edge clearance. Check the printer's actual usable area and slicer footprint, especially if adding a brim. Print at 100% scale.

The eight sections connect with through-thickness **dovetail joints** along the narrow bands. Each has a 14 mm head behind an 8 mm neck, so the sections cannot pull straight apart in the faceplate plane. Lower the flat sections together from above; the sockets have 0.25 mm nominal clearance. Actual printer fit may differ. Dry-fit all sections and check both openings against the bezel and grille before using the assembled pattern. These are pattern sections, not a verified replacement for the final wood faceplate.

Regenerate with `build.py` using the project's CadQuery environment. [Validation](validation.json) records individual STL bounds, watertight checks, two four-body plate layouts, and CAD non-overlap checks. Physical printer scale and joint fit remain to be tested.
