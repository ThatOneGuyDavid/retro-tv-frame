"""Verify current local fabrication files, assembly evidence and relative links."""
from pathlib import Path
import hashlib
import json
import re
import trimesh as tm

ROOT=Path(__file__).resolve().parents[1]
errors=[]
checked=0
for folder in ['bezel','knobs','grille']:
    for path in (ROOT/'design'/folder).glob('*.stl'):
        mesh=tm.load_mesh(path)
        if not mesh.is_watertight or mesh.volume<=0:
            errors.append('Invalid solid: '+str(path.relative_to(ROOT)))
        checked+=1
for name in ['bezel-left','bezel-right']:
    mesh=tm.load_mesh(ROOT/'design/bezel'/f'{name}.stl')
    if abs(mesh.bounds[0,2])>1e-5:errors.append(name+' is not on print Z0')
assembly=json.loads((ROOT/'design/assembly/validation.json').read_text())
if len(assembly['pair_checks'])!=210:errors.append('Expected 210 assembly pair checks')
for pair,result in assembly['pair_checks'].items():
    if result['intersection_mm3']>=.05:errors.append('Interference: '+pair)
for name,digest in assembly['source_sha256'].items():
    path=ROOT/'design'/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        errors.append('Assembly source changed: '+name)
bezel=json.loads((ROOT/'design/bezel/validation.json').read_text())['design']
if bezel['locator_count']!=8 or bezel['post_count']!=12:errors.append('Fitting feature count mismatch')
if bezel['inner_lip_underside_z_mm']!=1:errors.append('Glass-gap datum changed')
if bezel['joint_min_inner_edge_clearance_mm']<6:errors.append('Joint too close to opening')
template=json.loads((ROOT/'design/faceplate/validation.json').read_text())
if template['pdf_pages']!=11 or template['closed_cut_contours']!=3 or template['other_layer_outlines']!=0:
    errors.append('Clean template content mismatch')
if any(abs(x-25.4)>1e-8 for x in template['scale_mm_per_inch']):errors.append('Template scale mismatch')
for path in ROOT.rglob('*.md'):
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
        target=target.split('#',1)[0]
        if not target or '://' in target or target.startswith('mailto:'):continue
        if not (path.parent/target).exists():errors.append(f'Broken link in {path.relative_to(ROOT)}: {target}')
if errors:raise SystemExit('\n'.join(errors))
print(f'PASS: {checked} STL solids; print Z0; 210 assembly pairs; fitting features; template scale/content; local links.')
