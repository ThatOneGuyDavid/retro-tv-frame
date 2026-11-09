"""Modular retro control knob prototype; millimeters. No shaft assumed."""
from pathlib import Path
import json
import numpy as np
import trimesh as tm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

OUT=Path(__file__).resolve().parent

def box(size,xyz):
    m=tm.creation.box(size);m.apply_translation(xyz);return m

def cyl(r,h,z=0,x=0,y=0):
    m=tm.creation.cylinder(radius=r,height=h,sections=192)
    m.apply_translation([x,y,z+h/2]);return m

def union(*ms):return tm.boolean.union(list(ms),engine='manifold')
def diff(m,*cuts):return tm.boolean.difference([m]+list(cuts),engine='manifold')

def radial(profile,flutes=0):
    # Nonzero center radius prevents degenerate triangles; fill tiny axis separately.
    a=np.linspace(0,2*np.pi,768,endpoint=False);v=[]
    for r,z,depth in profile:
        rr=r-depth*(.5+.5*np.cos(flutes*a)) if flutes else np.full(len(a),r)
        v.extend(np.column_stack((rr*np.cos(a),rr*np.sin(a),np.full(len(a),z))))
    n=len(a);f=[]
    for j in range(len(profile)):
        k=(j+1)%len(profile)
        for i in range(n):
            q=(i+1)%n;f.extend([[j*n+i,j*n+q,k*n+q],[j*n+i,k*n+q,k*n+i]])
    m=tm.Trimesh(v,f,process=True);tm.repair.fix_normals(m);return m

# Stationary black dial plate: recessed outer trim seat and paint-filled scale.
plate=union(cyl(38,1.6),cyl(34,2.4,1.6))
tick_angles=np.linspace(225,-45,25)
ticks=[]
for i,deg in enumerate(tick_angles):
    length=4 if i%3==0 else 2.5
    b=box([length,.9,1.0],[31.5,0,3.9])
    b.apply_transform(tm.transformations.rotation_matrix(np.deg2rad(deg),[0,0,1]))
    ticks.append(b)
plate=diff(plate,cyl(6,6,-1),*ticks)
# Two mounting holes hidden by the grip. Counterbores for small screw heads.
for x in [-15,15]:
    plate=diff(plate,cyl(1.7,6,-1,x),cyl(3.3,1.8,2.4,x))

trim=diff(cyl(37.8,2.4),cyl(34.2,4,-.5))

# Knob body: 64 rounded fine flutes, chamfered ends, 46 mm maximum OD.
body=radial([(0.1,0,0),(21.6,0,0),(23,1.4,.35),
             (23,15.6,.35),(22,18,0),(0.1,18,0)],flutes=64)
body=union(body,cyl(.2,18))
body=diff(body,cyl(9.2,10,-1),cyl(20,3,16))
# Rear hub mounting: two provisional M3 self-tapping pilot bores.
for x in [-13,13]: body=diff(body,cyl(1.3,9,-1,x))
# No pointer socket or separate miniature pointer.

# Separate paintable face cap: gently raised conical face.
cap=radial([(.1,0,0),(19.8,0,0),(19.8,1.6,0),(.1,2.8,0)])
cap=union(cap,cyl(.2,2.8))
# Recessed index stripe for contrasting paint, integral to the center cap.
cap=diff(cap,box([1.6,6.5,2.4],[0,14.25,2.3]))

# Blank replaceable shaft hub. Hardware-specific shaft hole deferred deliberately.
hub=union(cyl(17,3),cyl(9,8,3))
for x in [-13,13]: hub=diff(hub,cyl(1.7,5,-1,x),cyl(3.2,1.8,0,x))

parts={'dial-plate':plate,'brass-trim':trim,'fluted-grip':body,
       'center-cap':cap,'blank-hub':hub}

def components(m):
    p=list(range(len(m.vertices)))
    def root(i):
        while p[i]!=i:p[i]=p[p[i]];i=p[i]
        return i
    for a,b in m.edges:p[root(int(a))]=root(int(b))
    return len({root(i) for i in range(len(p))})

report={}
for name,m in parts.items():
    assert m.is_watertight and m.volume>0 and components(m)==1,name
    # Print coordinates, all bottoms at Z0; retain XY centers except tiny pointer.
    m.export(OUT/f'{name}.stl')
    report[name]={'watertight':bool(m.is_watertight),'surface_components':components(m),
                 'positive_volume':bool(m.volume>0),'bounds_mm':m.extents.round(3).tolist(),
                 'solid_volume_cm3':round(m.volume/1000,3)}

# Assembly coordinates: plate rear Z0; grip rear Z9. Hub flange Z6..9.
placements={'dial-plate':0,'brass-trim':1.6,'fluted-grip':9,
            'center-cap':25,'blank-hub':6}
scene=tm.Scene()
for name,m in parts.items():
    q=m.copy();q.apply_translation([0,0,placements[name]])
    scene.add_geometry(q,node_name=name,geom_name=name)
scene.export(OUT/'knob-assembly.glb')
# Verify component clearances in the proposed assembly; hardware is not modeled.
assembly={}
for name,m in parts.items():
    q=m.copy();q.apply_translation([0,0,placements[name]]);assembly[name]=q
intersections={}
names=list(assembly)
for i,a in enumerate(names):
    for b in names[i+1:]:
        hit=tm.boolean.intersection([assembly[a],assembly[b]],engine='manifold')
        volume=abs(hit.volume) if len(hit.faces) else 0
        assert volume<.01,(a,b,volume)
        intersections[a+' / '+b]=round(float(volume),6)
report['assembly_checks']={'pair_intersection_volume_mm3':intersections,
                           'hardware_and_rotation_tested':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')

# Preview uses the exact radial dimensions, with assembly and finishing notes.
fig=plt.figure(figsize=(14,8),facecolor='#f3efe5')
ax=fig.add_axes([.04,.19,.43,.62]);ax.set_aspect('equal');ax.set_axis_off()
gold='#b69240';dark='#24241f'
ax.add_patch(Circle((0,0),38,color=dark))
ax.add_patch(Circle((0,0),37.8,facecolor=gold))
ax.add_patch(Circle((0,0),34.2,facecolor=dark))
for i,deg in enumerate(tick_angles):
    a=np.deg2rad(deg);length=4 if i%3==0 else 2.5
    ax.plot([(31.5-length/2)*np.cos(a),(31.5+length/2)*np.cos(a)],
            [(31.5-length/2)*np.sin(a),(31.5+length/2)*np.sin(a)],color=gold,lw=2)
ax.add_patch(Circle((0,0),23,facecolor=gold,edgecolor='#775f2a',lw=2))
for a in np.linspace(0,2*np.pi,64,endpoint=False):
    ax.plot([21.8*np.cos(a),22.8*np.cos(a)],[21.8*np.sin(a),22.8*np.sin(a)],color='#79612b',lw=.8)
ax.add_patch(Circle((0,0),19.8,facecolor='#caa95c',edgecolor='#e2c682',lw=1))
ax.add_patch(Rectangle((-.8,11),1.6,6.5,facecolor='#24241f'))
ax.set(xlim=(-43,43),ylim=(-43,43),title='FRONT · 76 mm dial / 46 mm grip')
ax=fig.add_axes([.53,.28,.43,.53]);ax.set_axis_off()
layers=[('Center cap + index',2.8,'Brass finish; recessed stripe filled with paint'),
        ('Fluted grip',18,'64 fine flutes; brass or dark bronze'),
        ('Removable rear hub',11,'Blank until control shaft is selected'),
        ('Wider outer trim ring',2.4,'3.6 mm wide × 2.4 mm thick; separate finish'),
        ('Fixed dial plate',4,'Black satin; recessed ticks paint-filled gold')]
for i,(name,h,desc) in enumerate(layers):
    y=5-i
    ax.add_patch(Rectangle((0,y-.2),1.3,.33,facecolor=gold if i in [0,1,3] else dark))
    ax.text(1.55,y+.04,name,fontsize=12,weight='bold')
    ax.text(1.55,y-.23,desc,fontsize=10)
ax.set(xlim=(0,9),ylim=(-.6,5.6))
fig.text(.05,.94,'RETRO CONTROLS · MODULAR PARTS',fontsize=21,weight='bold')
fig.text(.05,.89,'Two matching controls · wider brass trim and painted index · adaptable rear shaft hub',fontsize=12)
fig.text(.05,.10,'Five printed pieces per knob. Dimensions in millimeters; fit parts before finishing.',fontsize=12)
fig.text(.05,.055,'CAD-derived front layout; finishing colors are illustrative. No channel numbers or control labels assigned yet.',fontsize=10)
fig.savefig(OUT/'knob-preview.png',dpi=150);plt.close(fig)

# Exploded 3D drawing from actual triangle meshes.
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(10,10),facecolor='#f3efe5');ax=fig.add_subplot(projection='3d')
exploded={'dial-plate':0,'brass-trim':9,'blank-hub':19,'fluted-grip':39,'center-cap':65}
colors={'dial-plate':'#30302b','brass-trim':'#b79743','blank-hub':'#77776d',
        'fluted-grip':'#b79743','center-cap':'#c9ad68','pointer':'#ece4b5'}
for name,m in parts.items():
    verts=m.triangles.copy();verts[:,:,2]+=exploded[name]
    ax.add_collection3d(Poly3DCollection(verts,facecolor=colors[name],edgecolor='none',rasterized=True))
ax.set(xlim=(-42,42),ylim=(-42,42),zlim=(0,82));ax.set_box_aspect((84,84,100));ax.view_init(elev=23,azim=-65)
ax.set_axis_off();ax.set_title('EXPLODED CAD ASSEMBLY · ONE KNOB',fontsize=17)
fig.savefig(OUT/'knob-exploded.png',dpi=140);plt.close(fig)
print(json.dumps(report,indent=2))
