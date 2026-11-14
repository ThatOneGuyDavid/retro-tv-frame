"""Verify current local fabrication files, assembly evidence and relative links."""
from pathlib import Path
import hashlib
import json
import re
import trimesh as tm
import numpy as np

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
    flat=np.all(np.isclose(mesh.triangles[:,:,2],0,atol=1e-6),axis=1)
    if mesh.area_faces[flat].sum()<1000:errors.append(name+' has no substantial flat printing land')
    if not np.all(mesh.face_normals[flat,2]<-.99):errors.append(name+' bed faces do not face down')
assembly=json.loads((ROOT/'design/assembly/validation.json').read_text())
if any(abs(a-b)>1e-5 for a,b in zip(assembly['faceplate_size_mm'],[816.2,434.75])):
    errors.append('Faceplate size mismatch')
if abs(assembly['gaps']['trim_to_knob_plate_right_mm']-15)>1e-5:
    errors.append('Control-side margin mismatch')
if any(abs(a-b)>1e-5 for a,b in zip(assembly['frame']['outside_size_mm'],[842.1,460.65])):
    errors.append('Frame size mismatch')
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
if any(abs(a-b)>1e-5 for a,b in zip(template['panel_size_mm'],[816.2,434.75])):
    errors.append('Letter template size mismatch')
if template['pdf_pages']!=11 or template['closed_cut_contours']!=3 or template['other_layer_outlines']!=0:
    errors.append('Clean template content mismatch')
if any(abs(x-25.4)>1e-8 for x in template['scale_mm_per_inch']):errors.append('Template scale mismatch')
for folder,expected in [('faceplate-a1-and-eight',8),('faceplate-seven',7)]:
    report=json.loads((ROOT/'design'/folder/'validation.json').read_text())
    if any(abs(a-b)>1e-5 for a,b in zip(report['faceplate_outer_mm'],[816.2,434.75])):
        errors.append(folder+' panel size mismatch')
    if len(report['parts'])!=expected:errors.append(folder+' section count mismatch')
    for name in report['parts']:
        path=ROOT/'design'/folder/name
        if not path.exists():
            if not name.endswith('.stl'):path=ROOT/'design'/folder/(name+'.stl')
        mesh=tm.load_mesh(path)
        if not mesh.is_watertight or len(mesh.split())!=1 or max(mesh.extents[:2])>420:
            errors.append(folder+' invalid section: '+name)
    if folder=='faceplate-a1-and-eight':
        if report['pdf_pages']!=1 or len(report['build_plates'])!=2:
            errors.append('A1/eight pattern layout mismatch')
for path in ROOT.rglob('*.md'):
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
        target=target.split('#',1)[0]
        if not target or '://' in target or target.startswith('mailto:'):continue
        if not (path.parent/target).exists():errors.append(f'Broken link in {path.relative_to(ROOT)}: {target}')
if errors:raise SystemExit('\n'.join(errors))
print(f'PASS: {checked} printed STL solids; 210 assembly pairs; 15 mm margin; Letter, A1/eight and seven-piece patterns; local links.')
