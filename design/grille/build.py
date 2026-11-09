"""Flat, single-piece speaker grille prototype; units mm."""
from pathlib import Path
import json
import numpy as np
import trimesh as tm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Circle,Rectangle

OUT=Path(__file__).resolve().parent
WIDTH,HEIGHT=100.,160.
FLANGE=16.
THICK=3.
HOLE=4.8
PITCH=7.

def rounded(w,h,r,z,height):
    pts=[]
    for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),
                        (-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for a in np.linspace(start,start+90,25):
            pts.append([cx+r*np.cos(np.deg2rad(a)),cy+r*np.sin(np.deg2rad(a))])
    n=len(pts);v=[[x,y,z] for x,y in pts]+[[x,y,z+height] for x,y in pts]
    f=[]
    for i in range(1,n-1):f.extend([[0,i+1,i],[n,n+i,n+i+1]])
    for i in range(n):
        j=(i+1)%n;f.extend([[i,j,n+j],[i,n+j,n+i]])
    m=tm.Trimesh(v,f,process=True);tm.repair.fix_normals(m);return m

def cylinder(x,y,r):
    c=tm.creation.cylinder(radius=r,height=THICK+2,sections=48)
    c.apply_translation([x,y,THICK/2]);return c

centers=[(float(x),float(y)) for x in (np.arange(12)-5.5)*PITCH for y in (np.arange(20)-9.5)*PITCH]
mounts=[(x,y) for x in [-30.,30.] for y in [-88.,88.]]
body=rounded(WIDTH,HEIGHT+2*FLANGE,8,0,THICK)
cuts=[cylinder(x,y,HOLE/2) for x,y in centers]
# Four horizontal capsule mounting slots, Ø3.6 × 7.6 mm.
for x,y in mounts:
    b=tm.creation.box([4,3.6,THICK+2]);b.apply_translation([x,y,THICK/2])
    cuts += [tm.boolean.union([cylinder(x-2,y,1.8),cylinder(x+2,y,1.8),b],engine='manifold')]
body=tm.boolean.difference([body]+cuts,engine='manifold')

samplebox=tm.creation.box([42,42,10]);samplebox.apply_translation([0,0,2])
sample=tm.boolean.intersection([body,samplebox],engine='manifold')
sample.apply_translation(-sample.bounds[0])
# Exact wood opening outline, visual template only; not a selected cut tolerance.
outline=[]
shape=rounded(WIDTH,HEIGHT,8,0,1)
outline=shape.vertices[:len(shape.vertices)//2,:2]

def components(m):
    p=list(range(len(m.vertices)))
    def root(i):
        while p[i]!=i:p[i]=p[p[i]];i=p[i]
        return i
    for a,b in m.edges:p[root(int(a))]=root(int(b))
    return len({root(i) for i in range(len(p))})

report={}
for name,m in [('speaker-grille',body),('perforation-test',sample)]:
    assert m.is_watertight and m.volume>0 and components(m)==1,name
    m.export(OUT/f'{name}.stl')
    report[name]={'watertight':bool(m.is_watertight),'surface_components':components(m),
                 'positive_volume':bool(m.volume>0),'bounds_mm':m.extents.round(3).tolist()}
openarea=len(centers)*np.pi*(HOLE/2)**2
visiblearea=WIDTH*HEIGHT-(4-np.pi)*8**2
report['pattern']={'hole_count':len(centers),'hole_diameter_mm':HOLE,'pitch_mm':PITCH,
                   'minimum_web_mm':PITCH-HOLE,'visible_open_area_percent':round(100*openarea/visiblearea,1)}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')

fig,axs=plt.subplots(1,2,figsize=(11,8),facecolor='#f3efe5')
gold='#bb984b'
for ax,rear in zip(axs,[False,True]):
    w,h=(100,192) if rear else (100,160)
    ax.add_patch(FancyBboxPatch((-w/2,-h/2),w,h,boxstyle=f'round,pad=0,rounding_size={8}',facecolor=gold,edgecolor='#785d28',lw=2))
    for x,y in centers:ax.add_patch(Circle((x,y),HOLE/2,color='#25241e'))
    if rear:
        ax.add_patch(FancyBboxPatch((-50,-80),100,160,boxstyle='round,pad=0,rounding_size=8',fill=False,edgecolor='#725628',linestyle='--',lw=1.5))
        for x,y in mounts:
            ax.plot([x-2,x+2],[y,y],color='#25241e',lw=4,solid_capstyle='round')
    ax.set(xlim=(-75,75),ylim=(-105,105),aspect='equal')
    ax.set_axis_off();ax.set_title('REAR · top/bottom mounting bands' if rear else 'FRONT · wood conceals flange',fontsize=13)
fig.suptitle('SPEAKER GRILLE ·  TOP/BOTTOM MOUNTS',fontsize=18,weight='bold')
fig.text(.10,.10,'100 × 160 mm visible  |  100 × 192 × 3 mm overall  |  one flat print',fontsize=12)
fig.text(.10,.06,'240 holes · Ø4.8 mm · 2.2 mm webs · 27% visible open area · proposed dimensions',fontsize=11)
fig.tight_layout(rect=(0,.13,1,.94));fig.savefig(OUT/'grille-preview.png',dpi=150);plt.close(fig)
print(json.dumps(report,indent=2))
