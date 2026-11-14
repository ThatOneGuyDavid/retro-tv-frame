"""Faceplate sections from the user's approximate red split marks; mm."""
from pathlib import Path
from itertools import combinations
import json
import numpy as np
import cadquery as cq
import trimesh

OUT=Path(__file__).resolve().parent
LEFT,RIGHT,BOTTOM,TOP=-348.6,467.6,-224.375,210.375
THICKNESS=1.25
SCREEN_W,SCREEN_H=640.,369.
SPEAKER_X,SPEAKER_Y=392.5,-102.
NECK,HEAD,DEPTH,GAP=4.,7.,9.,.25

def screen_point_on_top(x):
    return SCREEN_H/2*(1-(abs(x)/(SCREEN_W/2))**8)**(1/8)
def screen_point_on_bottom(x):
    return -screen_point_on_top(x)
def screen_point_on_side(y,sign):
    return sign*SCREEN_W/2*(1-(abs(y)/(SCREEN_H/2))**8)**(1/8)
def squircle(w,h):
    a=np.linspace(0,2*np.pi,512,endpoint=False)
    c,s=np.cos(a),np.sin(a)
    c[abs(c)<1e-12]=0;s[abs(s)<1e-12]=0
    return np.column_stack((w/2*np.sign(c)*abs(c)**.25,
                            h/2*np.sign(s)*abs(s)**.25))
def rounded(w,h,r,cx,cy):
    p=[]
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),
                      (-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for a in np.linspace(start,start+90,25):
            p.append([cx+x+r*np.cos(np.deg2rad(a)),cy+y+r*np.sin(np.deg2rad(a))])
    return np.array(p)
def solid(points):
    return cq.Workplane('XY').polyline([tuple(p) for p in points]).close().extrude(THICKNESS)
screen=squircle(SCREEN_W,SCREEN_H)
speaker=rounded(100,160,8,SPEAKER_X,SPEAKER_Y)
panel=(cq.Workplane('XY').box(RIGHT-LEFT,TOP-BOTTOM,THICKNESS,
                             centered=(False,False,False))
       .translate((LEFT,BOTTOM,0)).cut(solid(screen)).cut(solid(speaker)))

# Clean mm coordinates inferred from the annotated screenshot, not measured
# cut requirements. Each split runs straight across the material band only.
cuts=[
    {'name':'top-left','outer':(-180.,TOP),'inner':(-180.,screen_point_on_top(-180)),
     'normal':(1,0)},
    {'name':'top-right','outer':(140.,TOP),'inner':(140.,screen_point_on_top(140)),
     'normal':(1,0)},
    {'name':'right','outer':(RIGHT,10.),'inner':(screen_point_on_side(10,1),10.),
     'normal':(0,-1)},
    {'name':'bottom-right','outer':(165.,BOTTOM),'inner':(165.,screen_point_on_bottom(165)),
     'normal':(-1,0)},
    {'name':'bottom-left','outer':(-200.,BOTTOM),'inner':(-200.,screen_point_on_bottom(-200)),
     'normal':(-1,0)},
    {'name':'left-bottom','outer':(LEFT,-90.),'inner':(screen_point_on_side(-90,-1),-90.),
     'normal':(0,1)},
    {'name':'left-top','outer':(LEFT,80.),'inner':(screen_point_on_side(80,-1),80.),
     'normal':(0,1)}]
corners=[[],[(RIGHT,TOP)],[(RIGHT,BOTTOM)],[],[(LEFT,BOTTOM)],[],[(LEFT,TOP)]]
names=['top-center','upper-control','lower-control-speaker',
       'bottom-center','lower-left','left-center','upper-left']
parts={}
for i,name in enumerate(names):
    j=(i+1)%len(cuts)
    outline=[(0,0),cuts[i]['inner'],cuts[i]['outer'],
             *corners[i],cuts[j]['outer'],cuts[j]['inner']]
    parts[name]=panel.intersect(solid(outline))

def dovetail(x,y,normal,clearance=0):
    nx,ny=normal;tx,ty=-ny,nx
    n=NECK+clearance;h=HEAD+clearance
    profile=[(-clearance,-n),(2,-n),(DEPTH+clearance,-h),
             (DEPTH+clearance,h),(2,n),(-clearance,n)]
    return solid([(x+u*nx+v*tx,y+u*ny+v*ty) for u,v in profile])

for i,cut in enumerate(cuts):
    before=names[(i-1)%len(names)]
    after=names[i]
    x=(cut['outer'][0]+cut['inner'][0])/2
    y=(cut['outer'][1]+cut['inner'][1])/2
    parts[before]=parts[before].union(dovetail(x,y,cut['normal']))
    parts[after]=parts[after].cut(dovetail(x,y,cut['normal'],GAP))

report={'faceplate_outer_mm':[RIGHT-LEFT,TOP-BOTTOM],
        'screen_opening_mm':[SCREEN_W,SCREEN_H],
        'speaker_opening_mm':[100,160],
        'split_coordinates_approximate':True,
        'cuts':[{'name':c['name'],'outer_mm':c['outer'],'inner_mm':c['inner']}
                for c in cuts],
        'dovetail_head_mm':2*HEAD,'dovetail_neck_mm':2*NECK,
        'socket_clearance_mm':GAP,'parts':{}}
for name,part in parts.items():
    path=OUT/(name+'.stl')
    part.val().exportStl(str(path),tolerance=.04,angularTolerance=.15)
    mesh=trimesh.load(path,force='mesh')
    assert mesh.is_watertight and len(mesh.split())==1,name
    report['parts'][name]={'bounds_mm':[[round(float(v),3) for v in row]
                                        for row in mesh.bounds],
                           'size_mm':[round(float(v),3) for v in mesh.extents]}
for (an,a),(bn,b) in combinations(parts.items(),2):
    assert a.intersect(b).val().Volume()<1e-5,(an,bn)

(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':report['parts'],'cuts':report['cuts']},indent=2))
