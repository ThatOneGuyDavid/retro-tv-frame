"""One-sheet paper and eight-part full-faceplate print pattern. Units: mm."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import cadquery as cq
import trimesh
from itertools import combinations
from matplotlib.collections import PolyCollection

OUT = Path(__file__).resolve().parent
SCREEN_W, SCREEN_H = 640.0, 369.0
SPEAKER_W, SPEAKER_H, SPEAKER_R = 100.0, 160.0, 8.0
SPEAKER_X, SPEAKER_Y = 392.5, -102.0
KNOB_X, KNOB_YS = 392.5, (130.0, 40.0)
LEFT, RIGHT = -348.6, 467.6
BOTTOM, TOP = -224.375, 210.375
THICKNESS = 3.175  # same nominal 1/8 inch faceplate as assembly-v9
NECK_HALF, HEAD_HALF, DEPTH, GAP = 4.0, 7.0, 9.0, 0.25

def squircle(w, h):
    # Match the 512-point assembly/template-v2 screen contour exactly.
    a = np.linspace(0, 2*np.pi, 512, endpoint=False)
    c, s = np.cos(a), np.sin(a)
    c[abs(c) < 1e-12] = 0
    s[abs(s) < 1e-12] = 0
    return np.column_stack((w/2*np.sign(c)*abs(c)**.25,
                            h/2*np.sign(s)*abs(s)**.25))

def rounded(w, h, r, cx=0, cy=0):
    points = []
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),
                      (-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for a in np.linspace(start,start+90,25):
            points.append([cx+x+r*np.cos(np.deg2rad(a)),
                           cy+y+r*np.sin(np.deg2rad(a))])
    return np.array(points)

screen = squircle(SCREEN_W, SCREEN_H)
speaker = rounded(SPEAKER_W, SPEAKER_H, SPEAKER_R, SPEAKER_X, SPEAKER_Y)

# A1 landscape, 1:1. Calibration marks sit inside the screen void.
PAGE_W, PAGE_H = 841.0, 594.0
fig = plt.figure(figsize=(PAGE_W/25.4,PAGE_H/25.4))
ax = fig.add_axes([0,0,1,1])
outer = np.array([[LEFT,BOTTOM],[RIGHT,BOTTOM],[RIGHT,TOP],[LEFT,TOP],[LEFT,BOTTOM]])
ax.plot(outer[:,0],outer[:,1],color='black',lw=.7)
for contour in (screen, speaker):
    closed = np.vstack((contour, contour[0]))
    ax.plot(closed[:,0], closed[:,1], color='black', lw=.7)
ax.plot([-50,50],[0,0], color='black', lw=.8)
for x in (-50,0,50):
    ax.plot([x,x],[-3,3], color='black', lw=.6)
ax.text(0,12,'100 mm SCALE CHECK',ha='center',fontsize=10)
square = np.array([[100,-12],[125.4,-12],[125.4,13.4],[100,13.4],[100,-12]])
ax.plot(square[:,0],square[:,1],color='black',lw=.7)
ax.text(112.7,-21,'25.4 mm SQUARE',ha='center',fontsize=8)
for y,label in zip(KNOB_YS,('UPPER','LOWER')):
    ax.plot([KNOB_X-4,KNOB_X+4],[y,y],color='#555',lw=.6)
    ax.plot([KNOB_X,KNOB_X],[y-4,y+4],color='#555',lw=.6)
    ax.text(KNOB_X,y+9,f'{label} KNOB CENTER (REFERENCE)',
            ha='center',fontsize=9,color='#555')
ax.text(-320,267,'FACEPLATE OUTLINE + CUTOUTS  |  FRONT / TOP UP  |  A1 LANDSCAPE  |  PRINT AT 100%',fontsize=12)
ax.set(xlim=((LEFT+RIGHT)/2-PAGE_W/2,(LEFT+RIGHT)/2+PAGE_W/2),ylim=(-297,297),aspect='equal')
ax.set_axis_off()
with PdfPages(OUT/'faceplate-cutouts-a1-one-sheet.pdf') as pdf:
    pdf.savefig(fig)
plt.close(fig)

def solid(points):
    return cq.Workplane('XY').polyline([tuple(p) for p in points]).close().extrude(THICKNESS)

panel = (cq.Workplane('XY').box(RIGHT-LEFT,TOP-BOTTOM,THICKNESS,
                              centered=(False,False,False))
         .translate((LEFT,BOTTOM,0)).cut(solid(screen)).cut(solid(speaker)))
parts = {}
for name,x0,x1,y0,y1 in [
    ('left-top.stl',LEFT,-320,0,TOP),
    ('left-bottom.stl',LEFT,-320,BOTTOM,0),
    ('top-left.stl',-320,0,0,TOP),
    ('top-right.stl',0,320,0,TOP),
    ('bottom-left.stl',-320,0,BOTTOM,0),
    ('bottom-right.stl',0,320,BOTTOM,0),
    ('controls-top.stl',320,RIGHT,0,TOP),
    ('controls-speaker.stl',320,RIGHT,BOTTOM,0)]:
    clip = (cq.Workplane('XY').box(x1-x0,y1-y0,THICKNESS,
                                   centered=(False,False,False))
            .translate((x0,y0,0)))
    parts[name] = panel.intersect(clip)

# Each dovetail head is wider than its neck. The receiver has a matching
# through-thickness socket, allowing flat parts to be lowered together in Z.
def dovetail(x, y, normal, clearance=0):
    nx,ny = normal
    tx,ty = -ny,nx
    neck = NECK_HALF + clearance
    head = HEAD_HALF + clearance
    end = DEPTH + clearance
    start = -clearance
    profile = [(start,-neck),(2,-neck),(end,-head),
               (end,head),(2,neck),(start,neck)]
    return solid([(x+u*nx+v*tx,y+u*ny+v*ty) for u,v in profile])

def join(owner, receiver, x, y, normal):
    tab = dovetail(x,y,normal)
    socket = dovetail(x,y,normal,GAP)
    parts[owner] = parts[owner].union(tab)
    parts[receiver] = parts[receiver].cut(socket)

join('left-top.stl','top-left.stl',-320,198,(1,0))
join('bottom-left.stl','left-bottom.stl',-320,-203,(-1,0))
join('top-left.stl','top-right.stl',0,198,(1,0))
join('bottom-right.stl','bottom-left.stl',0,-203,(-1,0))
join('top-right.stl','controls-top.stl',320,198,(1,0))
join('controls-speaker.stl','bottom-right.stl',320,-203,(-1,0))
join('left-top.stl','left-bottom.stl',-334,0,(0,-1))
join('controls-speaker.stl','controls-top.stl',400,0,(0,1))
report = {'source_geometry':'design/faceplate/build.py and design/assembly/build.py',
          'screen_cutout_mm':[SCREEN_W,SCREEN_H],
          'speaker_cutout_mm':[SPEAKER_W,SPEAKER_H],
          'speaker_center_mm':[SPEAKER_X,SPEAKER_Y],
          'knob_center_references_mm':[[KNOB_X,y] for y in KNOB_YS],
          'pdf_page_mm':[PAGE_W,PAGE_H], 'pdf_pages':1,
          'faceplate_outer_mm':[RIGHT-LEFT,TOP-BOTTOM],
          'printed_thickness_mm':THICKNESS,
          'dovetail_neck_width_mm':2*NECK_HALF,
          'dovetail_head_width_mm':2*HEAD_HALF,
          'dovetail_depth_mm':DEPTH,'socket_clearance_mm':GAP,
          'split_mm':{'x':[-320,0,320], 'center_y':0},
          'parts':{}}
for name, part in parts.items():
    path = OUT/name
    print_part = part
    print_part.val().exportStl(str(path),tolerance=.04,angularTolerance=.15)
    mesh = trimesh.load(path,force='mesh')
    size = mesh.extents
    assert mesh.is_watertight and len(mesh.split()) == 1, name
    assert size[0] <= 420 and size[1] <= 420, (name,size)
    report['parts'][name] = {'size_mm':[round(float(v),3) for v in size],
                             'print_rotation_deg':0,
                             'watertight':mesh.is_watertight,
                             'single_body':True}

# Two verified print layouts. XY coordinates are lower-left bounds in the
# slicer's 420 mm square build area; parts are printed as separate bodies.
layouts = {
    'plate-1-outer-sections.stl': [
        ('controls-speaker.stl',0,10,10),
        ('controls-top.stl',0,175,10),
        ('left-top.stl',0,330,10),
        ('left-bottom.stl',0,380,10)],
    'plate-2-screen-edges.stl': [
        ('bottom-right.stl',45,16,12),
        ('top-left.stl',270,192,20),
        ('bottom-left.stl',90,96,8),
        ('top-right.stl',90,14,84)]}
report['build_plates'] = {}
fig,axes=plt.subplots(1,2,figsize=(12,6))
for ax,(filename,placements) in zip(axes,layouts.items()):
    located=[]
    for name,angle,x,y in placements:
        shape=parts[name].val().rotate((0,0,0),(0,0,1),angle)
        b=shape.BoundingBox()
        shape=shape.translate((x-b.xmin,y-b.ymin,0))
        b=shape.BoundingBox()
        assert b.xmin>=0 and b.ymin>=0 and b.xmax<=420 and b.ymax<=420
        located.append((name,shape))
    for (name_a,a),(name_b,b) in combinations(located,2):
        assert a.intersect(b).Volume()<1e-5,(filename,name_a,name_b)
    compound=cq.Compound.makeCompound([shape.Solids()[0] for _,shape in located])
    compound.exportStl(str(OUT/filename),tolerance=.04,angularTolerance=.15)
    plate_mesh=trimesh.load(OUT/filename,force='mesh')
    assert len(plate_mesh.split())==4,filename
    report['build_plates'][filename] = {
        'body_count':4,
        'placements':[{'part':name,'rotation_deg':angle,
                       'lower_left_mm':[x,y]} for name,angle,x,y in placements],
        'pairwise_intersection':False}
    for name,shape in located:
        # Use the already validated source STL for a light, readable preview.
        mesh=trimesh.load(OUT/name,force='mesh')
        angle=next(p[1] for p in placements if p[0]==name)
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(angle),[0,0,1]))
        mesh.apply_translation([shape.BoundingBox().xmin-mesh.bounds[0,0],
                                shape.BoundingBox().ymin-mesh.bounds[0,1],0])
        vertices=mesh.vertices[mesh.faces]
        top=(np.ptp(vertices[:,:,2],axis=1)<1e-5)&(vertices[:,0,2]>1)
        ax.add_collection(PolyCollection(vertices[top][:,:,:2],facecolor='#849452',edgecolor='none'))
    ax.set(xlim=(0,420),ylim=(0,420),aspect='equal',title=filename.replace('.stl',''))
    ax.grid(color='#ddd')
fig.tight_layout()
fig.savefig(OUT/'two-plate-layout.png',dpi=140)
plt.close(fig)
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
