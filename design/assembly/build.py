"""Whole-front fit study and true-scale US Letter template. Units mm.
Current bezel, knobs, generic measured display envelope, and wooden frame.
"""
from pathlib import Path
import json, math, hashlib
import numpy as np
import trimesh as tm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
import base64

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
WOOD=3.175
GLUE=.2
WOOD_REAR=30+GLUE
WOOD_FRONT=WOOD_REAR+WOOD
CX=392.5
KNOB_Y=[130.,40.]
PLATE_Y=90.
GRILLE_Y=-102.
FRAME_WIDTH=19.05
FRAME_DEPTH=76.2
GROOVE_DEPTH=6.35
EDGE_ALLOWANCE=.25
IL,IR,IB,IT=-342.5,448.5,-218.275,204.275
OL,OR,OB,OT=IL-FRAME_WIDTH,IR+FRAME_WIDTH,IB-FRAME_WIDTH,IT+FRAME_WIDTH
FRAME_FRONT=WOOD_FRONT+3
FRAME_REAR=FRAME_FRONT-FRAME_DEPTH
LEFT,RIGHT=IL-GROOVE_DEPTH+EDGE_ALLOWANCE,IR+GROOVE_DEPTH-EDGE_ALLOWANCE
BOTTOM,TOP=IB-GROOVE_DEPTH+EDGE_ALLOWANCE,IT+GROOVE_DEPTH-EDGE_ALLOWANCE
WIDTH,HEIGHT=RIGHT-LEFT,TOP-BOTTOM
TRIM_WIDTH=FRAME_WIDTH
TRIM_THICK=FRAME_DEPTH

def box(size,center):
    m=tm.creation.box(size);m.apply_translation(center);return m
def cyl(r,h,x,y,z):
    m=tm.creation.cylinder(radius=r,height=h,sections=96)
    m.apply_translation([x,y,z+h/2]);return m
def extrude(points,z,h):
    n=len(points);v=[[x,y,z] for x,y in points]+[[x,y,z+h] for x,y in points]
    f=[]
    for i in range(1,n-1):f.extend([[0,i+1,i],[n,n+i,n+i+1]])
    for i in range(n):
        j=(i+1)%n;f.extend([[i,j,n+j],[i,n+j,n+i]])
    m=tm.Trimesh(v,f,process=True);tm.repair.fix_normals(m);return m
def rounded(w,h,r,cx=0,cy=0):
    p=[]
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for a in np.linspace(start,start+90,25):
            p.append([cx+x+r*np.cos(np.deg2rad(a)),cy+y+r*np.sin(np.deg2rad(a))])
    return np.array(p)
def squircle(w,h,n=8):
    # Exactly the same polygon sampling as approved bezel, for matching cut contour.
    a=np.linspace(0,2*np.pi,512,endpoint=False);c,s=np.cos(a),np.sin(a)
    c[abs(c)<1e-12]=0;s[abs(s)<1e-12]=0
    return np.column_stack((w/2*np.sign(c)*abs(c)**(2/n),h/2*np.sign(s)*abs(s)**(2/n)))
def diff(m,*cuts):return tm.boolean.difference([m]+list(cuts),engine='manifold')
def placed(path,xyz):
    m=tm.load_mesh(path);m.apply_translation(xyz);return m

screen_cut=squircle(640,369)  # wood overlaps approved 641 × 370 rim by 0.5 mm on axes
grille_cut=rounded(100,160,8,CX,GRILLE_Y)
plate_outline=rounded(108,186,8,CX,PLATE_Y)
wood=box([WIDTH,HEIGHT,WOOD],[(LEFT+RIGHT)/2,(BOTTOM+TOP)/2,(WOOD_REAR+WOOD_FRONT)/2])
wood=diff(wood,extrude(screen_cut,WOOD_REAR-1,WOOD+2),extrude(grille_cut,WOOD_REAR-1,WOOD+2),
          *[cyl(6,WOOD+2,CX,y,WOOD_REAR-1) for y in KNOB_Y])
# Front knob plate, glued flat to the thin wooden skin. No structural wood screws.
plate_z=WOOD_FRONT+GLUE
plate=extrude(rounded(108,186,8),0,3)
plate=diff(plate,*[cyl(6,5,0,y-PLATE_Y,-1) for y in KNOB_Y])
plate.export(OUT/'knob-mounting-plate.stl')
plate_mounted=plate.copy();plate_mounted.apply_translation([CX,PLATE_Y,plate_z])
wood.export(OUT/'wood-faceplate-reference.stl')

# Example display dimensions; glass is Z0 and raised factory face Z7.
ACTIVE_W,ACTIVE_H=596.9,336.55
MON_W,MON_H=ACTIVE_W+66,ACTIVE_H+82
MON_CY=-7.
monitor=diff(box([MON_W,MON_H,44],[0,MON_CY,-15]),
             box([ACTIVE_W,ACTIVE_H,8.2],[0,0,3.1]))
glass=box([ACTIVE_W,ACTIVE_H,1],[0,0,-.5])
display=tm.boolean.union([monitor,glass],engine='manifold')
assert display.is_watertight and display.volume>0
display.export(ROOT/'display/display-reference.stl')
parts={'display':display,'wood':wood,'bezel':placed(ROOT/'bezel/bezel-assembled.stl',[0,0,0]),
       'grille':placed(ROOT/'grille/speaker-grille.stl',[CX,GRILLE_Y,27]),
       'knob-mounting-plate':plate_mounted}
# Four true 45-degree mitered rails, each with the same faceplate groove.
groove=box([IR-IL+2*GROOVE_DEPTH,IT-IB+2*GROOVE_DEPTH,WOOD+.4],
           [(IL+IR)/2,(IB+IT)/2,(WOOD_REAR+WOOD_FRONT)/2])
rail_shapes={
    'top':[(OL,OT),(OR,OT),(IR,IT),(IL,IT)],
    'bottom':[(OL,OB),(IL,IB),(IR,IB),(OR,OB)],
    'left':[(OL,OB),(OL,OT),(IL,IT),(IL,IB)],
    'right':[(OR,OB),(IR,IB),(IR,IT),(OR,OT)]}
for label,outline in rail_shapes.items():
    rail=diff(extrude(np.array(outline),FRAME_REAR,FRAME_DEPTH),groove)
    rail.export(OUT/f'wood-frame-{label}-reference.stl')
    parts['wood-frame-'+label]=rail
for sign,label in [(-1,'bottom'),(1,'top')]:
    parts['joining-key-'+label]=placed(ROOT/'bezel/joining-key.stl',[0,sign*176,10.1])
knob_base=plate_z+3+GLUE
knob_offsets={'dial-plate':0,'brass-trim':1.6,'fluted-grip':9,'center-cap':25,'blank-hub':6}
for i,y in enumerate(KNOB_Y,1):
    for name,z in knob_offsets.items():
        parts[f'knob-{i}/{name}']=placed(ROOT/f'knobs/{name}.stl',[CX,y,knob_base+z])

colors={'display':[35,40,41,255],'wood':[138,84,42,255],'bezel':[122,131,44,255],
        'joining-key-top':[105,163,196,255],'joining-key-bottom':[105,163,196,255],
        'grille':[188,151,68,255],**{'wood-frame-'+x:[100,59,30,255] for x in rail_shapes},'knob-mounting-plate':[48,46,38,255]}
scene=tm.Scene()
manifest={}
for name,m in parts.items():
    assert m.is_watertight and m.volume>0,name
    q=m.copy()
    color=colors.get(name,[190,154,71,255])
    if 'dial-plate' in name:color=[35,34,28,255]
    if 'blank-hub' in name:color=[100,100,90,255]
    q.visual.vertex_colors=np.tile(color,(len(q.vertices),1))
    scene.add_geometry(q,node_name=name,geom_name=name)
    manifest[name]={'bounds_mm':m.bounds.round(4).tolist(),'watertight':True,'positive_volume':True}
scene.export(OUT/'front-assembly.glb')

# Self-contained browser viewer: actual triangle meshes, no CDN or server needed.
viewer_data=[]
for name,m in parts.items():
    data=np.concatenate((m.triangles.reshape(-1,3),np.repeat(m.face_normals,3,axis=0)),axis=1).astype('<f4')
    color=colors.get(name,[190,154,71,255])
    if 'dial-plate' in name:color=[35,34,28,255]
    if 'blank-hub' in name:color=[100,100,90,255]
    viewer_data.append({'name':name,'data':base64.b64encode(data.tobytes()).decode(),
                        'color':[v/255 for v in color[:3]],'count':len(data)})
html='''<!doctype html><meta charset="utf-8"><title>Retro TV assembly</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#ece8db;color:#292c23;font:14px system-ui;overflow:hidden}
main{display:flex;width:100vw;height:100vh;height:100dvh;min-height:0}
aside{flex:0 0 270px;width:270px;padding:18px;overflow:auto;background:#f8f5eb;border-right:1px solid #d7d4c6}
h1{font-size:19px;line-height:1.25;margin:0 0 10px}.help{font-size:12px;line-height:1.5;color:#626457;margin:8px 0 16px}
.view-buttons{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:14px}button{padding:8px;border:1px solid #bbb8aa;border-radius:4px;background:#fffdf6;color:inherit;cursor:pointer}button:hover{background:#e9e6d8}button:focus-visible,input:focus-visible,summary:focus-visible{outline:2px solid #7b863b;outline-offset:2px}
.zoom-control{margin:14px 0}.zoom-control label{display:flex;justify-content:space-between;font-size:13px}.zoom-control input{width:100%;margin:8px 0;accent-color:#7b863b}.zoom-control output{font-variant-numeric:tabular-nums}.pattern-control{display:block;font-size:13px;margin:12px 0}.dimensions{margin:14px 0;padding:10px 0;border-top:1px solid #ddd9cc;border-bottom:1px solid #ddd9cc;font-size:12px;line-height:1.5}.dimensions p{margin:8px 0;color:#626457}
aside details{margin:6px 0}aside summary{cursor:pointer;font-size:13px;padding:3px 0}aside input[type=checkbox]{vertical-align:middle;margin-right:5px}.layer-children{margin-left:13px;padding-left:7px;border-left:1px solid #d7d4c6}.layer-leaf{display:block;font-size:13px;padding:3px 0;margin:3px 0}
canvas{flex:1;width:0;min-width:0;height:100%;display:block;touch-action:none}
@media(max-width:600px){aside{flex-basis:210px;width:210px;padding:12px}.layer-children{margin-left:8px;padding-left:5px}}
</style>
<main><aside aria-label="Assembly controls">
<h1>Retro TV assembly</h1><p class="help">Drag to rotate.<br>Scroll to zoom. Use the tree to show or hide parts.</p>
<div class="view-buttons"><button id="front">Front</button><button id="rear">Rear</button><button id="angled">Angled</button><button id="fit">Fit view</button></div>
<div class="zoom-control"><label for="zoom">Zoom <output id="zoom-value" for="zoom">100%</output></label><input id="zoom" type="range" min="25" max="300" step="1" value="100"></div>
<label class="pattern-control"><input id="testpattern" type="checkbox" checked> Retro test pattern</label>
<details class="dimensions"><summary>Dimensions and notes</summary><p>Wood: 1/8 inch<br>Display: 662.9 × 418.55 × 44 mm<br>Faceplate: 803.2 × 434.75 mm<br>Frame stock: 3/4 × 3 inch<br>Inner lip underside: 1 mm above glass</p><p>Geometry in millimeters. Display uses a square-edged envelope. Stand and internal hardware are not modeled.</p></details>
<section id="parts" aria-label="Layer visibility"><strong>Layers</strong></section>
</aside><canvas id="view" aria-label="Interactive 3D assembly"></canvas></main>
<script>const raw=__DATA__;const c=document.getElementById('view'),g=c.getContext('webgl',{antialias:true});
if(!g){document.getElementById('parts').textContent='WebGL unavailable. Use assembly-front.png or front-assembly.glb.';throw Error('WebGL unavailable')}
const vs=`attribute vec3 p;attribute vec3 n;uniform vec2 angle;uniform float zoom,aspect;varying vec3 normal;varying vec3 localPosition;varying vec3 localNormal;
vec3 rotate(vec3 a){float cy=cos(angle.x),sy=sin(angle.x),cx=cos(angle.y),sx=sin(angle.y);vec3 b=vec3(cy*a.x+sy*a.z,a.y,-sy*a.x+cy*a.z);return vec3(b.x,cx*b.y-sx*b.z,sx*b.y+cx*b.z);}
void main(){vec3 q=rotate(p-vec3(59.5,-7.,10.));gl_Position=vec4(q.x*zoom/aspect,q.y*zoom,-q.z/1500.,1.);normal=rotate(n);localPosition=p;localNormal=n;}`;
const fs=`precision mediump float;
uniform vec3 color;
uniform float screen;
varying vec3 normal;
varying vec3 localPosition;
varying vec3 localNormal;
vec3 bars(float x){
 float i=floor(clamp(x,0.,.9999)*7.);
 if(i<1.)return vec3(.82);if(i<2.)return vec3(.9,.84,.08);
 if(i<3.)return vec3(.06,.78,.82);if(i<4.)return vec3(.08,.74,.17);
 if(i<5.)return vec3(.8,.12,.7);if(i<6.)return vec3(.85,.09,.07);
 return vec3(.08,.15,.8);
}
vec3 testCard(vec2 uv){
 vec3 v=bars(uv.x);
 if(uv.y<.3&&uv.y>=.22){float i=floor(uv.x*7.);v=mod(i,2.)<1.?bars(1.-uv.x):vec3(.035);}
 if(uv.y<.22){float level=floor(uv.x*8.)/7.;v=vec3(.05+.9*level);if(uv.y<.07)v=mod(floor(uv.x*28.),2.)<1.?vec3(.04):vec3(.92);}
 vec2 p=vec2((uv.x-.5)*1.7736,uv.y-.57);
 float ring=1.-smoothstep(.0015,.0035,abs(length(p)-.255));
 float cross=(1.-smoothstep(.001,.0025,min(abs(p.x),abs(p.y))))*(1.-smoothstep(.25,.26,length(p)));
 v=mix(v,vec3(.96),max(ring,cross)*.65);
 // Softer phosphor-like palette: subdued chroma, luminance and warm whites.
 float luma=dot(v,vec3(.299,.587,.114));
 v=mix(vec3(luma),v,.57)*.73;
 v*=vec3(1.,.965,.90);
 v*=.98+.02*sin(uv.y*1000.);
 return v;
}
void main(){
 if(screen>.5&&abs(localPosition.z)<.01&&localNormal.z>.9&&abs(localPosition.x)<298.451&&abs(localPosition.y)<168.276){
  vec2 uv=localPosition.xy/vec2(596.9,336.55)+.5;
  gl_FragColor=vec4(testCard(uv),1.);
 }else{float d=.35+.65*abs(dot(normalize(normal),normalize(vec3(-.3,.4,1.))));gl_FragColor=vec4(color*d,1.);}
}
`;
function shader(type,s){const t=g.createShader(type);g.shaderSource(t,s);g.compileShader(t);if(!g.getShaderParameter(t,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(t));return t}
const program=g.createProgram();g.attachShader(program,shader(g.VERTEX_SHADER,vs));g.attachShader(program,shader(g.FRAGMENT_SHADER,fs));g.linkProgram(program);if(!g.getProgramParameter(program,g.LINK_STATUS))throw Error(g.getProgramInfoLog(program));g.useProgram(program);
const loc={};for(const x of ['angle','zoom','aspect','color','screen'])loc[x]=g.getUniformLocation(program,x);
const pos=g.getAttribLocation(program,'p'),nor=g.getAttribLocation(program,'n');g.enableVertexAttribArray(pos);g.enableVertexAttribArray(nor);g.enable(g.DEPTH_TEST);
let yaw=-.18,pitch=.18,zoom=1/500;
const parts=raw.map(o=>{const bytes=Uint8Array.from(atob(o.data),x=>x.charCodeAt(0));o.buffer=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,o.buffer);g.bufferData(g.ARRAY_BUFFER,new Float32Array(bytes.buffer),g.STATIC_DRAW);delete o.data;o.visible=true;
return o});
const leafLabel=name=>({display:'Display',wood:'Faceplate','knob-mounting-plate':'Knob mounting plate','grille-v2':'Speaker grille',grille:'Speaker grille','dial-plate':'Dial plate','brass-trim':'Brass trim','fluted-grip':'Fluted grip','center-cap':'Center cap','blank-hub':'Rear hub'}[name.split('/').pop()]||name.replace(/-/g,' '));
const leaf=part=>({key:part.name,label:leafLabel(part.name),part});
const matching=fn=>parts.filter(p=>fn(p.name)).map(leaf);
const layerRoot={key:'all',label:'Complete assembly',open:true,children:[
 ...matching(n=>n==='display'),...matching(n=>n==='wood'),
 {key:'green',label:'Green bezel and joints',children:matching(n=>n.startsWith('bezel')||n.startsWith('joining-key'))},
 {key:'right-section',label:'Controls and speaker',open:true,children:[
 {key:'controls',label:'Controls',open:true,children:[
  ...matching(n=>n==='knob-mounting-plate'),
  {key:'upper-knob',label:'Upper knob',children:matching(n=>n.startsWith('knob-1/'))},
  {key:'lower-knob',label:'Lower knob',children:matching(n=>n.startsWith('knob-2/'))}]},
  ...matching(n=>n.startsWith('grille'))]},
 {key:'frame',label:'Wooden frame',children:matching(n=>n.startsWith('wood-frame-'))}]};
function descendants(node){return node.part?[node.part]:node.children.flatMap(descendants)}
const assigned=new Set(descendants(layerRoot).map(p=>p.name));
const extra=parts.filter(p=>!assigned.has(p.name));if(extra.length)layerRoot.children.push({key:'other',label:'Other parts',children:extra.map(leaf)});
const layerNodes=new Map();
function syncLayerChecks(){for(const node of layerNodes.values()){const items=descendants(node),count=items.filter(p=>p.visible).length;node.checkbox.checked=count===items.length;node.checkbox.indeterminate=count>0&&count<items.length}}
function setLayerVisibility(node,visible){for(const part of descendants(node))part.visible=visible;syncLayerChecks();draw()}
function renderLayer(node,parent){
 const input=document.createElement('input');input.type='checkbox';input.checked=true;input.setAttribute('aria-label',node.label);input.addEventListener('click',e=>e.stopPropagation());input.onchange=()=>setLayerVisibility(node,input.checked);node.checkbox=input;layerNodes.set(node.key,node);
 if(node.part){const label=document.createElement('label');label.className='layer-leaf';label.append(input,document.createTextNode(' '+node.label));parent.append(label)}
 else{const details=document.createElement('details');details.open=!!node.open;const summary=document.createElement('summary');summary.append(input,document.createTextNode(' '+node.label));details.append(summary);const children=document.createElement('div');children.className='layer-children';for(const child of node.children)renderLayer(child,children);details.append(children);parent.append(details)}
}
renderLayer(layerRoot,document.getElementById('parts'));syncLayerChecks();

function draw(){syncZoom();const d=devicePixelRatio||1;c.width=Math.round(c.clientWidth*d);c.height=Math.round(c.clientHeight*d);g.viewport(0,0,c.width,c.height);g.clearColor(.925,.91,.86,1);g.clear(g.COLOR_BUFFER_BIT|g.DEPTH_BUFFER_BIT);g.uniform2f(loc.angle,yaw,pitch);g.uniform1f(loc.zoom,zoom);g.uniform1f(loc.aspect,c.width/c.height);
for(const o of parts){if(!o.visible)continue;g.bindBuffer(g.ARRAY_BUFFER,o.buffer);g.vertexAttribPointer(pos,3,g.FLOAT,false,24,0);g.vertexAttribPointer(nor,3,g.FLOAT,false,24,12);g.uniform3fv(loc.color,o.color);g.uniform1f(loc.screen,o.name==='display'&&document.getElementById('testpattern').checked?1:0);
g.drawArrays(g.TRIANGLES,0,o.count)}}
document.getElementById('front').onclick=()=>{yaw=0;pitch=0;draw()};document.getElementById('rear').onclick=()=>{yaw=Math.PI;pitch=0;draw()};document.getElementById('angled').onclick=()=>{yaw=-.3;pitch=.3;draw()};
let drag=false,x=0,y=0;c.onpointerdown=e=>{drag=true;x=e.clientX;y=e.clientY;c.setPointerCapture(e.pointerId)};c.onpointerup=()=>drag=false;c.onpointermove=e=>{if(!drag)return;yaw+=(e.clientX-x)*.006;pitch+=(e.clientY-y)*.006;x=e.clientX;y=e.clientY;draw()};c.onwheel=e=>{e.preventDefault();zoom=Math.max(baseZoom()*.25,Math.min(baseZoom()*3,zoom*Math.exp(-e.deltaY*.001)));draw()};document.getElementById('testpattern').onchange=draw;function baseZoom(){return Math.min(1.75*(c.clientWidth/c.clientHeight)/829.1,1.75/460.65)}
function syncZoom(){const percent=Math.round(100*zoom/baseZoom());document.getElementById('zoom').value=Math.max(25,Math.min(300,percent));document.getElementById('zoom-value').textContent=percent+'%'}
function fitView(){zoom=baseZoom();draw()}
document.getElementById('zoom').oninput=e=>{zoom=baseZoom()*Number(e.target.value)/100;draw()};document.getElementById('fit').onclick=fitView;window.addEventListener('resize',draw);fitView();</script>'''
(OUT/'assembly-viewer.html').write_text(html.replace('__DATA__',json.dumps(viewer_data)))

# Check every pair whose bounding boxes overlap. AABB exclusions are recorded too.
checks={};names=list(parts)
for i,a in enumerate(names):
    for b in names[i+1:]:
        aa,bb=parts[a].bounds,parts[b].bounds
        if np.any(np.minimum(aa[1],bb[1])-np.maximum(aa[0],bb[0]) <= 1e-6):
            checks[a+' / '+b]={'method':'separated bounding boxes','intersection_mm3':0.}
        else:
            hit=tm.boolean.intersection([parts[a],parts[b]],engine='manifold')
            vol=abs(float(hit.volume)) if len(hit.faces) else 0.
            assert vol < .05,(a,b,vol)
            checks[a+' / '+b]={'method':'solid intersection','intersection_mm3':round(vol,6)}

gaps={'bezel_to_grille_flange_x_mm':CX-50-340.5,
      'bezel_to_knob_plate_x_mm':CX-54-340.5,
      'lower_dial_to_grille_visible_y_mm':(40-38)-(GRILLE_Y+80),
      'screen_flange_to_wood_glue_gap_mm':GLUE,
      'grille_to_wood_glue_gap_mm':GLUE,
      'knob_plate_to_wood_glue_gap_mm':GLUE,
      'knob_plate_to_bezel_z_mm':plate_z-30,
      'trim_to_knob_plate_right_mm':IR-(CX+54),
      'trim_to_bezel_top_bottom_mm':min(IT-185,-185-IB),
      'trim_to_bezel_left_mm':-320.5-IL,
      'wood_edge_to_grille_bottom_mm':GRILLE_Y-96-BOTTOM}
assert gaps['bezel_to_grille_flange_x_mm']>=2
assert gaps['trim_to_knob_plate_right_mm']>=2
assert gaps['trim_to_bezel_top_bottom_mm']>=2
sources={}
for path in [ROOT/'bezel/bezel-assembled.stl',ROOT/'grille/speaker-grille.stl']+list((ROOT/'knobs').glob('*.stl')):
    sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()

# Common vector artwork for overview, SVG master, and all tiled PDF pages.
# Coordinates are assembly/world XY. Wood outline and holes are solid cut lines;
# component outlines are dashed placement lines, never additional wood cutouts.
def drawing(ax,detail=True):
    ax.add_patch(Rectangle((LEFT,BOTTOM),WIDTH,HEIGHT,fill=False,lw=.8,color='black'))
    ax.add_patch(Polygon(screen_cut,fill=False,lw=.8,color='black'))
    ax.add_patch(Polygon(grille_cut,fill=False,lw=.8,color='black'))
    ax.add_patch(Polygon(squircle(681,384),fill=False,lw=.5,ls='--',edgecolor='#777'))
    ax.add_patch(Polygon(rounded(100,192,8,CX,GRILLE_Y),fill=False,lw=.5,ls='--',edgecolor='#777'))
    ax.add_patch(Polygon(plate_outline,fill=False,lw=.7,ls='--',edgecolor='#555'))
    ax.add_patch(Rectangle((IL,IB),IR-IL,IT-IB,fill=False,lw=.6,ls='-.',edgecolor='#666'))
    for y in KNOB_Y:
        ax.add_patch(Circle((CX,y),6,fill=False,lw=.7,ls='--',edgecolor='#555'))
        ax.add_patch(Circle((CX,y),38,fill=False,lw=.5,ls='--',edgecolor='#555'))
        ax.plot([CX-9,CX+9],[y,y],color='black',lw=.4)
        ax.plot([CX,CX],[y-9,y+9],color='black',lw=.4)
    if detail:
        ax.text(-10,0,'SCREEN CUTOUT\n640 × 369 mm\n0.5 mm nominal rim overlap',ha='center',va='center',fontsize=9)
        ax.text(CX,GRILLE_Y,'GRILLE CUTOUT\n100 × 160 mm\nR8 corners',ha='center',va='center',fontsize=7)
        ax.text(CX,86,'Ø12 access holes\nShaft hardware TBD',ha='center',fontsize=6)
        ax.text(LEFT+6,TOP-10,'TOP / FRONT VIEW — solid: cut; dashed: placement only',fontsize=7,va='top')
    # Shared alignment crosses on a 100 mm world grid, visible on adjacent sheets.
    for x in np.arange(-300,491,100):
        for y in np.arange(-200,201,100):
            ax.plot([x-2,x+2],[y,y],color='#aaa',lw=.3)
            ax.plot([x,x],[y-2,y+2],color='#aaa',lw=.3)
    # Dedicated crosses within each shared overlap strip, not just the coarse grid.
    def cross(x,y,label):
        ax.plot([x-3,x+3],[y,y],color='#555',lw=.4)
        ax.plot([x,x],[y-3,y+3],color='#555',lw=.4)
        ax.text(x+4,y+3,label,fontsize=4,color='#555')
    for col in range(1,5):
        for row in range(2):
            for d in [45,175]:cross(LEFT+col*180.5+5,TOP-row*244-d,f'V{col}-{row+1}-{d}')
    for col in range(5):
        for d in [40,140]:cross(LEFT+col*180.5+d,TOP-244-5,f'H{col+1}-{d}')

fig,ax=plt.subplots(figsize=(14,7),facecolor='#f3efe5')
ax.add_patch(Rectangle((-MON_W/2,MON_CY-MON_H/2),MON_W,MON_H,facecolor='#353739'))
ax.add_patch(Rectangle((LEFT,BOTTOM),WIDTH,HEIGHT,facecolor='#a7774e'))
ax.add_patch(Polygon(squircle(641,370),facecolor='#7e8731',edgecolor='#484c22'))
screen_outline=Polygon(squircle(587,326,4),facecolor='#222',edgecolor='#111')
ax.add_patch(screen_outline)
# CAD presentation only: a clipped color-bar card on the viewing surface.
bar_colors=['#999489','#a29b49','#3e8b8a','#4a823f','#8d4778','#934338','#303c79']
for i,color in enumerate(bar_colors):
    patch=Rectangle((-298.45+i*596.9/7,-168.275),596.9/7,336.55,facecolor=color)
    patch.set_clip_path(screen_outline);ax.add_patch(patch)
for i in range(8):
    patch=Rectangle((-298.45+i*596.9/8,-168.275),596.9/8,74,facecolor=(lambda v:(v,v*.965,v*.90))(.73*(.05+.9*i/7)))
    patch.set_clip_path(screen_outline);ax.add_patch(patch)
ring=Circle((0,23.56),85.82,fill=False,color='#aba69a',lw=.8)
ring.set_clip_path(screen_outline);ax.add_patch(ring)
ax.add_patch(Polygon(grille_cut,facecolor='#bd984d',edgecolor='#765e2d'))
for x in (np.arange(12)-5.5)*7:
    for y in (np.arange(20)-9.5)*7:
        ax.add_patch(Circle((CX+x,GRILLE_Y+y),2.4,color='#27271f'))
ax.add_patch(Polygon(plate_outline,facecolor='#37342c',edgecolor='#1f1d17'))
for y in KNOB_Y:
    ax.add_patch(Circle((CX,y),38,facecolor='#b99543'))
    ax.add_patch(Circle((CX,y),34.2,facecolor='#23231e'))
    for deg in np.linspace(225,-45,25):
        a=np.deg2rad(deg)
        ax.plot([CX+30*np.cos(a),CX+33*np.cos(a)],[y+30*np.sin(a),y+33*np.sin(a)],color='#bd984d',lw=.7)
    ax.add_patch(Circle((CX,y),23,facecolor='#bc984e',edgecolor='#806632'))
    ax.add_patch(Circle((CX,y),19.8,facecolor='#cfaf66',edgecolor='#dfc37e'))
    ax.add_patch(Rectangle((CX-.8,y+11),1.6,6.5,facecolor='#222'))
ax.set(xlim=(LEFT-12,RIGHT+12),ylim=(-230,220),aspect='equal')
ax.set_axis_off();fig.suptitle('RETRO TV FRAME · MITERED GROOVED WOOD FRAME',fontsize=17,weight='bold')
# Four mitered front rail faces.
for outline in rail_shapes.values():
    ax.add_patch(Polygon(outline,facecolor='#754823',edgecolor='#563619',lw=.7))
ax.set(xlim=(OL-12,OR+12),ylim=(OB-12,OT+12))
fig.text(.08,.07,'Mitered 3/4 × 3 inch frame · 1/4 inch groove · 2 mm housing clearance · sculpted printable surround',fontsize=11)
fig.tight_layout(rect=(0,.1,1,.94));fig.savefig(OUT/'assembly-front.png',dpi=160);plt.close(fig)

fig,ax=plt.subplots(figsize=(14,7),facecolor='#f3efe5')
drawing(ax,False)
ax.text(130,-170,'Dashed: concealed flange envelopes',fontsize=9)
ax.annotate('2 mm flange gap',xy=(341.5,-100),xytext=(130,-110),arrowprops={'arrowstyle':'->'},fontsize=9)
ax.set(xlim=(LEFT-12,RIGHT+12),ylim=(-230,220),aspect='equal');ax.set_axis_off()
fig.suptitle('FIT STUDY · REAR ENVELOPES OVER FRONT VIEW (NOT MIRRORED)',fontsize=16)
fig.tight_layout();fig.savefig(OUT/'assembly-clearances.png',dpi=150);plt.close(fig)

# SVG's physical size is exactly the outer panel size. No automatic padding.
fig=plt.figure(figsize=(WIDTH/25.4,HEIGHT/25.4));ax=fig.add_axes([0,0,1,1])
drawing(ax);ax.set(xlim=(LEFT,RIGHT),ylim=(BOTTOM,TOP),aspect='equal');ax.set_axis_off()
fig.savefig(OUT/'faceplate-full-size.svg',format='svg');plt.close(fig)

PAGE_W,PAGE_H=215.9,279.4
MARGIN=12.7
TW,TH=PAGE_W-2*MARGIN,PAGE_H-2*MARGIN
OVERLAP=10.
SX,SY=TW-OVERLAP,TH-OVERLAP
COLS=math.ceil((WIDTH-OVERLAP)/SX);ROWS=math.ceil((HEIGHT-OVERLAP)/SY)
tiles=[]
with PdfPages(OUT/'faceplate-letter-tiled.pdf', metadata={'CreationDate':None,'ModDate':None}) as pdf:
    fig=plt.figure(figsize=(8.5,11))
    instructions=(
        'WOOD FACEPLATE — US LETTER TEMPLATE\n\n'
        'Print every page at ACTUAL SIZE / 100%.\n'
        'Disable Fit, Shrink, and Scale to printable area.\n'
        'Use 8.5 × 11 inch portrait paper, one-sided.\n\n'
        'First verify the 100 mm bar below with a ruler.\n'
        'The 1 inch square must measure 25.4 mm on both axes.\n'
        'If either dimension is wrong, do not use the template.\n\n'
        f'Tiles: {COLS} columns × {ROWS} rows; 10 mm overlap.\n'
        'Arrange row 1 above row 2; columns left to right.\n'
        'Trim ONE side of each shared margin, overlap the\n'
        'drawings, and match grid crosses and cut lines.\n'
        'Do not align by paper edges alone.\n\n'
        'SOLID black lines: outer wood boundary and cutouts.\n'
        'DASHED lines: component placement — DO NOT CUT.\n'
        'DASH-DOT rectangle: inside opening of frame.\n'
        'Dashed Ø12 access circles: leave undrilled until\n'
        'the control hardware and shaft support are selected.\n'
        'No fastener holes are needed for glued mounting.\n\n'
        'Panel: 803.2 × 434.75 mm; screen opening: 640 × 369 mm.\n'
        'Screen contour is curved, NOT a bounding rectangle.\n'
        'Grille opening: 100 × 160 mm, corner radius 8 mm.\n'
        'View is FRONT / TOP UP. Attach template to wood front.\n\n'
        'Dry-fit printed parts before cutting final material.\n'
        '1/8 inch wood shown in assembly; thinner is possible.\n'
        'Actual shaft hardware and glue performance untested.')
    fig.text(.085,.94,instructions,va='top',fontsize=10,linespacing=1.5)
    ax=fig.add_axes([MARGIN/PAGE_W,MARGIN/PAGE_H,TW/PAGE_W,45/PAGE_H])
    ax.plot([0,100],[20,20],color='black',lw=1)
    for x in [0,50,100]:ax.plot([x,x],[18,22],color='black');ax.text(x,24,str(x),ha='center',fontsize=8)
    ax.text(50,12,'100 mm check',ha='center',fontsize=9)
    ax.add_patch(Rectangle((140,8),25.4,25.4,fill=False,color='black'))
    ax.text(152.7,3,'1 inch square',ha='center',fontsize=8)
    ax.set(xlim=(0,TW),ylim=(0,45));ax.set_axis_off();pdf.savefig(fig);plt.close(fig)
    for row in range(ROWS):
        for col in range(COLS):
            x0=LEFT+col*SX;y1=TOP-row*SY
            fig=plt.figure(figsize=(8.5,11))
            ax=fig.add_axes([MARGIN/PAGE_W,MARGIN/PAGE_H,TW/PAGE_W,TH/PAGE_H])
            drawing(ax)
            ax.set(xlim=(x0,x0+TW),ylim=(y1-TH,y1),aspect='auto');ax.set_axis_off()
            # Explicit clip for text/artists as well as geometry.
            for artist in ax.get_children():
                if hasattr(artist,'set_clip_on'):artist.set_clip_on(True)
                if hasattr(artist,'set_clip_path'):artist.set_clip_path(ax.patch)
            if col>0:ax.axvline(x0+OVERLAP,color='#888',lw=.35,ls=':')
            if row>0:ax.axhline(y1-OVERLAP,color='#888',lw=.35,ls=':')
            fig.text(.06,.975,f'R{row+1} C{col+1}  |  FRONT / TOP UP  |  Actual size 100%  |  10 mm overlap',fontsize=8,va='top')
            # 50 mm scale bar on each tile, rendered in page coordinates.
            xfrac=.07; yfrac=.025
            from matplotlib.lines import Line2D
            fig.add_artist(Line2D([xfrac,xfrac+50/PAGE_W],[yfrac,yfrac],transform=fig.transFigure,color='black',lw=.8))
            fig.text(xfrac,yfrac+.006,'50 mm',fontsize=7)
            pdf.savefig(fig);plt.close(fig)
            tiles.append({'row':row+1,'column':col+1,'world_bounds_mm':[x0,y1-TH,x0+TW,y1]})


# Full measured-housing coverage and design clearances.
coverage={'monitor_bounds_mm':monitor.bounds.round(4).tolist(),
          'glass_bounds_mm':glass.bounds.round(4).tolist(),
          'top_faceplate_margin_beyond_housing_mm':round(TOP-(MON_CY+MON_H/2),4),
          'bottom_faceplate_margin_beyond_housing_mm':round((MON_CY-MON_H/2)-BOTTOM,4),
          'minimum_existing_bezel_z_mm':float(parts['bezel'].bounds[0,2]),
          'post_to_factory_front_glue_gap_mm':.2,
          'inner_lip_rear_above_glass_mm':1.,
          'joint_pocket_to_inner_opening_mm':8.,
          'required_joint_clearance_mm':6.,
          'requested_glass_clearance_mm':1.,
          'requested_standoffs':{'top':4,'bottom':4,'left':2,'right':2,'added':True}}
report={'wood_thickness_mm':WOOD,'glue_allowance_mm':GLUE,'faceplate_size_mm':[WIDTH,HEIGHT],
        'frame':{'stock_mm':[FRAME_WIDTH,FRAME_DEPTH],'groove_depth_mm':GROOVE_DEPTH,'groove_width_mm':WOOD+.4,'groove_edge_allowance_mm':EDGE_ALLOWANCE,'inside_bounds_xy_mm':[IL,IB,IR,IT],'outside_size_mm':[OR-OL,OT-OB],'front_z_mm':FRAME_FRONT,'rear_z_mm':FRAME_REAR,'housing_clearance_left_mm':-331.45-IL,'housing_clearance_top_mm':IT-202.275,'housing_clearance_bottom_mm':-216.275-IB,'bezel_flange_left_clearance_mm':-340.5-IL},
        'gaps':gaps,'template':{'total_pdf_pages':len(tiles)+1,'page_inches':[8.5,11],'columns':COLS,'rows':ROWS,'overlap_mm':10,'tiles':tiles},'parts':manifest,'pair_checks':checks,'source_sha256':sources,
        'display_fit':coverage,'new_cut_template_generated':True,
        'physical_fit_glue_strength_and_hardware_verified':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
(ROOT/'display/dimensions.json').write_text(json.dumps({
    'viewing_area_mm':[ACTIVE_W,ACTIVE_H],
    'factory_bezel_widths_mm':{'top':34,'bottom':48,'left':33,'right':33},
    'outer_size_mm':[MON_W,MON_H,44],
    'glass_front_z_mm':0,'factory_front_z_mm':7,'housing_back_z_mm':-37,
    'outer_center_xy_mm':[0,MON_CY],'glass_proxy_thickness_mm':1,
    'assumptions':['Square edges','44 mm is total front-to-back depth','Display and glass modeled as one solid unit','Stand omitted']},indent=2)+'\n')
print(json.dumps({'parts':len(parts),'pair_checks':len(checks),'display_fit':coverage},indent=2))

(OUT/'frame-cut-list.csv').write_text('part,quantity,stock_front_width_mm,stock_depth_mm,long_point_length_mm,short_point_length_mm,ends\n'
    +f'top_bottom,2,19.05,76.2,{OR-OL:.3f},{IR-IL:.3f},45 degree miters\n'
    +f'left_right,2,19.05,76.2,{OT-OB:.3f},{IT-IB:.3f},45 degree miters\n')
fig,ax=plt.subplots(figsize=(10,6),facecolor='#f3efe5')
# Top rail section: inward opening is at horizontal coordinate zero.
ax.add_patch(Rectangle((0,FRAME_REAR),FRAME_WIDTH,FRAME_DEPTH,facecolor='#a7774e',edgecolor='#563619'))
ax.add_patch(Rectangle((0,WOOD_REAR-.2),GROOVE_DEPTH,WOOD+.4,facecolor='#f3efe5',edgecolor='#563619'))
ax.add_patch(Rectangle((-18,WOOD_REAR),18+6.1,WOOD,facecolor='#cfb58d',edgecolor='#555'))
ax.add_patch(Rectangle((-36,-37),34,44,facecolor='#444',alpha=.7))
ax.annotate('Display edge: 2 mm inside rail',xy=(-2,7),xytext=(-35,16),arrowprops={'arrowstyle':'->'})
ax.annotate('Groove: 6.35 deep × 3.575 wide',xy=(6.35,31.5),xytext=(-35,48),arrowprops={'arrowstyle':'->'})
ax.annotate('3 mm faceplate setback\n2.8 mm front groove lip',xy=(0,FRAME_FRONT),xytext=(10,52),arrowprops={'arrowstyle':'->'})
ax.text(8,-5,'76.2 mm\nrail depth',ha='center')
ax.set(xlim=(-42,38),ylim=(-45,65),xlabel='Across rail (mm)',ylabel='Z from viewing glass (mm)',title='WOOD FRAME SECTION · TOP RAIL')
fig.tight_layout();fig.savefig(OUT/'frame-section.png',dpi=150);plt.close(fig)
