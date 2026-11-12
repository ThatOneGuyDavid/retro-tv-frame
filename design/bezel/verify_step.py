"""Round-trip STEP and compare deterministic surface samples with print STLs.
Requires build_step.py dependencies plus manifold3d and rtree==1.4.1.
"""
from pathlib import Path
import json
import cadquery as cq
import numpy as np
from OCP.BRepMesh import BRepMesh_IncrementalMesh
import trimesh as tm
OUT=Path(__file__).resolve().parent
report=json.loads((OUT/'step-validation.json').read_text())
for name,entry in report['parts'].items():
    shape=cq.importers.importStep(str(OUT/(name+'.step'))).val()
    BRepMesh_IncrementalMesh(shape.wrapped,.005,False,.03,True).Perform()
    vertices,faces=shape.tessellate(.005,.03)
    mesh=tm.Trimesh([[v.x,v.y,v.z] for v in vertices],faces,process=True)
    tm.repair.fix_normals(mesh)
    reference=tm.load_mesh(OUT/(name+'.stl'))
    assert mesh.is_watertight and reference.is_watertight
    volume_error=abs(shape.Volume()-reference.volume)/reference.volume
    entry['relative_volume_difference_from_stl']=volume_error
    entry['max_bounds_difference_from_stl_mm']=float(np.max(np.abs(mesh.bounds-reference.bounds)))
    distances=[]
    for source,target in [(mesh,reference),(reference,mesh)]:
        points,_=tm.sample.sample_surface(source,12000,seed=12345)
        ds=[]
        for chunk in np.array_split(points,48):
            ds.extend(tm.proximity.closest_point(target,chunk)[1])
        distances.extend(ds)
    entry['surface_comparison']={'samples_each_direction':12000,'seed':12345,'tessellation_absolute_linear_tolerance_mm':.005,'max_sampled_distance_mm':float(np.max(distances)),'p99_sampled_distance_mm':float(np.percentile(distances,99))}
    assert volume_error<.005,(name,volume_error)
    assert max(distances)<.15,(name,max(distances))
    print(name,entry,flush=True)
report['comparison_note']='Sampled comparison, not an exhaustive maximum-deviation proof. STEP is a smooth reconstruction, not an exact mesh conversion.'
(OUT/'step-validation.json').write_text(json.dumps(report,indent=2)+'\n')
