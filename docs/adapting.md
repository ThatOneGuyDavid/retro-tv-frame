# Adapt the design to another display

Start from the current **bezel v8** files in `design/bezel/`, including its flat inner printing land. The v8 test print was successful; each adaptation still needs its own print and fit checks.

This is a measured-envelope design, not a universal model that becomes correct by choosing a diagonal screen size. You can use the approach with other displays, but each adaptation needs its own fitting geometry and interference checks. No manufacturer or model name is needed.

## Measure the things that control fit

Use the same datum throughout: center of the viewing area, glass surface Z0. Record:

| Measurement | Your value |
| --- | --- |
| Actual viewing width and height | |
| Factory border width: left, right, top, bottom separately | |
| Raised frame height above viewing glass | |
| Total frontmost-to-rearmost body depth | |
| Corner radii, slopes, steps, curved/uneven surfaces | |
| Flat usable glue areas; buttons/vents/camera/sensors to avoid | |
| Stand, VESA, ports, cables and ventilation envelopes | |
| Required visible area and acceptable corner cropping | |
| Actual printer bed, exclusion zones, and support/brim allowance | |
| Actual wood/panel thickness, rail section and groove plan | |
| Speaker/control footprints and rear clearance | |

Front photographs and side profiles are useful, but do not substitute for measured dimensions. Mask labels, serials, logos or device metadata before sharing photos if you want to keep its identity private. For square borders, housing width is viewing width + left + right; height is viewing height + top + bottom. Housing center shifts by (right-left)/2 in X and (top-bottom)/2 in Y. With recess R and total depth D, factory face Z=R and rear Z=R-D.

## Adapt in this order

1. **Build the actual display envelope first.** Include all steps, corner shape and the true viewing recess, as one display unit. Use extra reference envelopes for stand/cables/vents where needed.
2. **Set the inner opening and glass gap.** Choose acceptable masking and a datum for the underside, not an ambiguous phrase such as “1 mm proud.” The example underside is Z1; the visible top is 2.4 mm higher.
3. **Shape one continuous surround.** Increase peak height or width when needed to clear the factory step. Do not insert a visible shelf merely to satisfy a clearance clamp. Test the whole surface, including corner transitions, against the housing. Opening shape and viewing-angle occlusion matter as well as collision.
4. **Place glue feet on verified usable frame surfaces.** Keep their footprint off glass. Contact Z must include the intended cured adhesive thickness. Height tolerances affect the inner gap.
5. **Add clearance-fit locating tabs.** Register against inner vertical factory walls; tips must stay off glass. Keep meaningful lead-ins and test actual printer tolerances. They should not become press-fit clamps or replace the height datum.
6. **Split for printing, then design joints.** Reserve actual supports/brim space. Keep the complete rear joint feature a defined distance from the inner edge (example requirement ≥6 mm, actual ≥7 mm), and clear of the housing. Preserve a continuous visible curve while adding local reinforcement behind it.
7. **Lay out every part as an assembly.** Check hidden flange envelopes, not just visible outlines. Include control plate, knobs, grille, wood, joints, and display before minimizing margins.
8. **Build the actual rearward wood rails and grooves.** Give the display and plastic clearance at their real Z positions. Panel size must include groove engagement; frame outside size must include stock width. Pick the groove's position along the rail depth explicitly.
9. **Generate the clean paper template from the same geometry.** Only wood cut contours plus tile registration. Verify true-scale PDF size and overlap coverage; measure a printed calibration page.
10. **Print local fit samples and dry-assemble.** Do this before full prints, final wood cutting, or permanent glue. Then finish and document the adapted measurements.

## Do not just scale the STLs

Uniform scaling changes holes, fitting clearances, lip height, key thickness, glue allowance, tab registration, and the groove relationship. Nonuniform scaling distorts those features further. Edit/regenerate the source geometry instead. Large imported meshes in an AI conversation are not proof that an adaptation fits; require numerical checks and inspect the resulting CAD.

The included Python source is the **complete example design**, with dimensional assumptions distributed across its builders. It is not a single-parameter universal generator. Updating only `display/build.py` will not automatically update the bezel, sample locations, controls, rails, template or checks. Use [the source map](source.md) and coordinate changes deliberately.

## Prompt suggestions

Replace bracketed values with measurements. These prompts work as specifications for a CAD-capable assistant; they are not image-generation prompts or guarantees of fit.

### Model the reference display

```text
Create a millimeter CAD reference of one intact display unit. Do not use a
manufacturer or model name. Viewing area is [W] × [H]. Factory borders are
left [L], right [R], top [T], bottom [B]. Glass is recessed [G] from the
factory front. Total body depth is [D]. Edges are [describe].
Use viewing-area center as X0/Y0 and glass front Z0. Derive the asymmetric
housing center and bounds. Include [stand/cable/vent] exclusion envelopes.
Export the reference model and a dimensions table before fitting anything.
```

### Adapt the sculpted bezel

```text
Adapt this repository's sculpted green bezel to the attached measured
display model. The UNDERSIDE of the inner lip must have [gap] mm air gap
above glass. Preserve a single continuous curved visible surface; adjust
outer height/width as needed to clear the factory frame without a shelf.
Keep the mounting flange outward-only and level with the outer peak.
Place [count] glue feet on specified flat factory-frame regions with
[adhesive] mm allowance. Add lead-in locators against the inner factory
walls with [clearance] mm clearance per side; keep tips [tip gap] above glass.
Show sections and check the complete shell, corners, feet and locators
against the display. Separate physical assumptions from CAD checks.
```

### Split and join it

```text
My usable printer bed is [X] × [Y], with [support/brim budget] reserved.
Split the bezel into printable parts. Keep the entire joining feature at
least [distance] mm from the inner opening, clear of the factory housing,
and hidden behind the smooth face. Include sample joints and locating
samples. Include a continuous FLAT underside printing land, not a knife edge.
For the example v8 the land is 2.2 mm top/bottom and 2.7 mm at the sides.
Export mm STLs with the complete flat contact surface at print Z0;
keep assembly-coordinate references separate. Reimport and verify substantial,
connected planar bed-contact area and first-layer brim generation, not only
the minimum Z coordinate. Check the STLs.
```

### Fit the wood and controls

```text
Keep the approved green print UNCHANGED. Use rails [front width] × [depth]
extending rearward, 45-degree mitered corners, and a [depth]-deep panel
groove at [position] behind the rail front. Actual panel thickness is [t].
Leave at least [gap] around the housing and hidden plastic at their true
depths. Choose explicit panel/groove allowances. Rebalance the speaker
and control column if needed. Model each rail and groove, check all part
pairs, and provide long-/short-point cut lengths and a rail section.
```

### Make the paper template and check the result

```text
Generate a faceplate-only cutting template from the approved wood geometry.
Include the panel boundary and final cutouts only, no other-layer outlines.
Keep tile alignment crosses, overlap guides, page identifiers and scale bars.
Use 8.5 × 11 inch portrait sheets, 1/2 inch margins, 10 mm overlaps, and a
100 mm bar plus a 1 inch square on a calibration page. Verify page dimensions,
true XY scale, full tile coverage, watertight positive-volume meshes,
assembly intersections and unchanged-part fingerprints. Explain what still
requires a physical fit check. Do not fabricate a design history or test results.
```
