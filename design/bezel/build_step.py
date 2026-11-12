"""Reconstruct the v8 bezel as curved B-rep solids; independent of mesh builder.
Requires cadquery==2.8.0, numpy, trimesh, scipy. Does not overwrite print STLs.
"""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

OUT = Path(__file__).resolve().parent

def bounds(shape):
    bb=Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped,bb,False,False)
    return np.array(bb.Get()).reshape(2,3)

def outline(t, z):
    w,h,n = (681.,384.,8.) if t == -1 else (641.-54*t,370.-44*t,8.-4*t)
    a=np.linspace(0,2*np.pi,513)
    c,s=np.cos(a),np.sin(a)
    c[abs(c)<1e-12]=0; s[abs(s)<1e-12]=0
    xy=np.column_stack((w/2*np.sign(c)*abs(c)**(2/n),h/2*np.sign(s)*abs(s)**(2/n)))
    edges=[]
    for q in range(4):
        points=[cq.Vector(x,y,z) for x,y in xy[q*128:q*128+129]]
        edges.append(cq.Edge.makeSplineApprox(points,tol=0.001,minDeg=3,maxDeg=6))
    return cq.Wire.assembleEdges(edges)

def front(t):
    return 3.4+26.6*((np.sqrt(1-t+.025)-np.sqrt(.025))/(np.sqrt(1.025)-np.sqrt(.025)))

def rear(t):
    return 1+(front(t)-3.4)*np.clip((.90-t)/.05,0,1)

def skin(ts, height):
    builder=BRepOffsetAPI_ThruSections(False,False,1e-6)
    builder.SetMaxDegree(3)
    for t in ts: builder.AddWire(outline(float(t),float(height(t))).wrapped)
    builder.Build()
    assert builder.IsDone()
    return cq.Shape.cast(builder.Shape()).Faces()

def box(size, center):
    return cq.Workplane('XY').box(*size).val().translate(center)

def clipped_box(size, center, envelope):
    return box(size,center).intersect(envelope)

print('Building curved shell',flush=True)
ts=np.linspace(0,1,17)
faces=skin(ts,front)
for lo,hi,count in [(0,.85,17),(.85,.90,7),(.90,1,2)]:
    faces += skin(np.linspace(lo,hi,count),rear)
for t in [0,1]:
    a,b=outline(t,front(t)),outline(t,rear(t))
    builder=BRepOffsetAPI_ThruSections(False,True,1e-6)
    builder.AddWire(a.wrapped);builder.AddWire(b.wrapped);builder.Build()
    faces+=cq.Shape.cast(builder.Shape()).Faces()
body=cq.Solid.makeSolid(cq.Shell.makeShell(faces))
if body.Volume()<0: body=cq.Shape.cast(body.wrapped.Reversed())
assert body.isValid(), 'shell invalid'
print('Shell',body.Volume(),len(body.Faces()),flush=True)
# Filled front envelope for trimming the feet, locators and joint pads.
print("Envelope",flush=True)
envelope_faces=skin(ts,front)
for t in [0,1]:
    builder=BRepOffsetAPI_ThruSections(False,True,1e-6)
    builder.AddWire(outline(t,0).wrapped)
    builder.AddWire(outline(t,front(t)).wrapped)
    builder.Build()
    envelope_faces+=cq.Shape.cast(builder.Shape()).Faces()
envelope_faces.append(cq.Face.makeFromWires(outline(0,0),[outline(1,0)]))
envelope=cq.Solid.makeSolid(cq.Shell.makeShell(envelope_faces))
if envelope.Volume()<0: envelope=cq.Shape.cast(envelope.wrapped.Reversed())
assert envelope.isValid()
print("Flange",flush=True)
flange=cq.Solid.extrudeLinear(outline(-1,27),[outline(0,27)],cq.Vector(0,0,3))
body=body.fuse(flange)
print("Joint pads",flush=True)
for y in [-176.,176.]:
    body=body.fuse(clipped_box([30,12,30],[0,y,25],envelope))
    body=body.cut(box([28,10,3],[0,y,9.7]))
print('Adding feet',flush=True)
posts=[(x,y) for y in [-176.5,176.5] for x in [-210.,-70.,70.,210.]]
posts += [(x,y) for x in [-310.5,310.5] for y in [-60.,60.]]
for x,y in posts:
    body=body.fuse(clipped_box([8,8,30],[x,y,22.2],envelope))
print('Adding locating tabs',flush=True)
for horizontal,sign,stations in [(True,1,[-140.,140.]),(True,-1,[-140.,140.]),(False,1,[-70.,70.]),(False,-1,[-70.,70.])]:
    outer=(168.275 if horizontal else 298.45)-.3
    inner=outer-1.8
    for station in stations:
        wires=[]
        for z,edge in [(3.,outer-.6),(4.,outer),(34.,outer)]:
            pts=[(along,sign*rad,z) if horizontal else (sign*rad,along,z)
                 for along,rad in [(station-4,inner),(station+4,inner),(station+4,edge),(station-4,edge)]]
            wires.append(cq.Wire.makePolygon([cq.Vector(*p) for p in pts],close=True))
        tab=cq.Solid.makeLoft(wires,ruled=True).intersect(envelope)
        body=body.fuse(tab)
body=body.clean()
assert body.isValid() and len(body.Solids())==1
parts={'bezel-assembled':body,'joining-key':box([27.6,9.6,1],[0,0,.5])}
for name,x in [('left',-250),('right',250)]:
    part=body.intersect(box([500,600,100],[x,0,20])).clean()
    # Preserve the original STL datum; spline bounding boxes can be conservative.
    parts['bezel-'+name]=part.translate((340.5 if name=='left' else 0,192.,-1.))
report={'method':'Curved B-rep reconstruction from v8 equations; original STLs unchanged', 'units':'mm','parts':{}}
for name,part in parts.items():
    assert part.isValid() and len(part.Solids())==1,name
    path=OUT/(name+'.step'); cq.exporters.export(part,str(path))
    imported=cq.importers.importStep(str(path)).val()
    assert imported.isValid() and len(imported.Solids())==1
    assert abs(imported.Volume()-part.Volume())/part.Volume()<1e-5, (name,part.Volume(),imported.Volume())
    bb=bounds(imported)
    report['parts'][name]={'valid':True,'solids':len(imported.Solids()),'faces':len(imported.Faces()),'volume_mm3':imported.Volume(),'pre_export_volume_mm3':part.Volume(),'bounds_mm':bb.tolist()}
    print(name,report['parts'][name],flush=True)
(OUT/'step-validation.json').write_text(json.dumps(report,indent=2)+'\n')
