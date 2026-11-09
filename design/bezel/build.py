"""Thin sculpted bezel fitted to measured display; mm, glass at Z0."""
from pathlib import Path
import json
import numpy as np
import trimesh as tm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle,Circle

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
N=512
LAND_T=.90
BLEND_T=.85
TS=np.unique(np.r_[np.linspace(0,1,97),BLEND_T,LAND_T])
SHELL=2.4
PEAK=30.

def contour(t):
    w,h=np.array([641.,370.])*(1-t)+np.array([587.,326.])*t
    n=8*(1-t)+4*t
    if t==-1:w,h,n=681.,384.,8.
    a=np.linspace(0,2*np.pi,N,endpoint=False);c,s=np.cos(a),np.sin(a)
    c[abs(c)<1e-12]=0;s[abs(s)<1e-12]=0
    return np.column_stack((w/2*np.sign(c)*abs(c)**(2/n),h/2*np.sign(s)*abs(s)**(2/n)))

def original_rear(t,xy):
    # Single analytic curve: no factory-clearance clamp or intermediate shelf.
    u=1-t
    curve=(np.sqrt(u+.025)-np.sqrt(.025))/(np.sqrt(1.025)-np.sqrt(.025))
    return np.full(len(xy),1+(PEAK-SHELL-1)*curve)

def rear(t,xy):
    # Permanent flat printing land, installed at Z1 above the glass.
    # Keep the original visible face; add material only beneath its inner rim.
    # Flat from t=.90 to 1 (2.2 mm top/bottom, 2.7 mm sides), with a short
    # underside blend returning to the original shell by t=.85.
    weight=np.clip((LAND_T-t)/(LAND_T-BLEND_T),0,1)
    return 1+(original_rear(t,xy)-1)*weight

def loft(loops):
    v=np.concatenate(loops);f=[]
    for j in range(len(loops)):
        k=(j+1)%len(loops)
        for i in range(N):
            q=(i+1)%N
            f.extend([[j*N+i,j*N+q,k*N+q],[j*N+i,k*N+q,k*N+i]])
    m=tm.Trimesh(v,f,process=True);tm.repair.fix_normals(m)
    assert m.is_watertight and m.volume>0
    return m

front=[];back=[]
for t in TS:
    xy=contour(t);z=rear(t,xy)
    back.append(np.column_stack((xy,z)))
    front.append(np.column_stack((xy,original_rear(t,xy)+SHELL)))
shell=loft(front+back[::-1])

def box(size,center):
    m=tm.creation.box(size);m.apply_translation(center);return m
def diff(m,*cuts):return tm.boolean.difference([m]+list(cuts),engine='manifold')
def union(*ms):return tm.boolean.union(list(ms),engine='manifold')

# Peak-level outward-only flange. No inward flange or deep skirt.
flange=loft([np.column_stack((contour(t),np.full(N,z))) for t,z in [(-1,27),(-1,30),(0,30),(0,27)]])
body=union(shell,flange)

# Local joint pads are behind the curve, 7 mm from the inner outline.
filled=loft(front+[np.column_stack((contour(1),np.zeros(N))),np.column_stack((contour(0),np.zeros(N)))])
for y in [-176.,176.]:
    pad=tm.boolean.intersection([box([30,12,30],[0,y,25]),filled],engine='manifold')
    body=union(body,pad)
    body=diff(body,box([28,10,3],[0,y,9.7]))  # floor Z11.2
key=box([27.6,9.6,1.0],[0,0,.5])

# Twelve glue points, all footprints wholly on the measured flat factory face.
# Contact plane Z7.2 reserves nominal 0.2 mm adhesive above factory Z7.
post_xy=[(x,y) for y in [-176.5,176.5] for x in [-210.,-70.,70.,210.]]
post_xy += [(x,y) for x in [-310.5,310.5] for y in [-60.,60.]]
posts=[];post_report=[]
# Exact under-shell envelope lets post tops follow the curved skin.
envelope=loft(front+[np.column_stack((contour(1),np.zeros(N))),
                     np.column_stack((contour(0),np.zeros(N)))])
for x,y in post_xy:
    # 8 × 8 mm glue foot; shell contact follows the envelope rather than poking through.
    post=tm.boolean.intersection([box([8,8,30],[x,y,22.2]),envelope],engine='manifold')
    assert post.volume>0
    posts.append(post)
    inside_glass=(abs(x)-4<298.45 and abs(y)-4<168.275)
    assert not inside_glass
    assert abs(x)+4<331.45 and y-4>-216.275 and y+4<202.275
    post_report.append({'center_xy_mm':[x,y],'foot_mm':[8,8],'contact_z_mm':7.2,
                        'foot_inside_factory_face':True})
body=union(body,*posts)

# Eight locating tabs enter the recess and register against its vertical inner walls.
# They never contact glass or replace the twelve adhesive height-setting feet.
LOCATOR_CLEARANCE=.3
locators=[];locator_report=[]
for edge,sign,stations in [('top',1,[-140.,140.]),('bottom',-1,[-140.,140.]),
                            ('right',1,[-70.,70.]),('left',-1,[-70.,70.])]:
    horizontal=edge in ['top','bottom']
    wall=168.275 if horizontal else 298.45
    outward=wall-LOCATOR_CLEARANCE
    inward=outward-1.8
    station_length=8.
    for station in stations:
        # Tip has 0.6 mm additional lead-in, joining full-width tab at Z4.
        vertices=[]
        for z,outer in [(3.,outward-.6),(4.,outward),(34.,outward)]:
            for along,rad in [(station-4,inward),(station+4,inward),
                              (station+4,outer),(station-4,outer)]:
                vertices.append([along,sign*rad,z] if horizontal else [sign*rad,along,z])
        faces=[[0,2,1],[0,3,2],[8,9,10],[8,10,11]]
        for layer in [0,1]:
            a=layer*4;b=(layer+1)*4
            for i in range(4):
                j=(i+1)%4;faces.extend([[a+i,a+j,b+j],[a+i,b+j,b+i]])
        tab=tm.Trimesh(vertices,faces,process=True);tm.repair.fix_normals(tab)
        tab=tm.boolean.intersection([tab,envelope],engine='manifold')
        assert tab.is_watertight and tab.volume>0
        locators.append(tab)
        locator_report.append({'edge':edge,'station_mm':station,'wall_clearance_mm':.3,
                               'tip_above_glass_mm':3.,'width_mm':8.,'radial_thickness_mm':1.8,
                               'lead_in_mm':.6})
body=union(body,*locators)

# Validate against the actual one-piece display.
display=tm.load_mesh(ROOT/'display/display-reference.stl')
hit=tm.boolean.intersection([body,display],engine='manifold')
assert len(hit.faces)==0 or abs(hit.volume)<.01
parts={}
for name,x in [('left',-250),('right',250)]:
    m=tm.boolean.intersection([body,box([500,600,100],[x,0,20])],engine='manifold')
    m.apply_translation(-m.bounds[0]);parts[name]=m;m.export(OUT/f'bezel-{name}.stl')
body.export(OUT/'bezel-assembled.stl');key.export(OUT/'joining-key.stl')
for name,x in [('left',-10),('right',10)]:
    sample=tm.boolean.intersection([body,box([20,24,40],[x,176,12])],engine='manifold')
    sample.apply_translation(-sample.bounds[0]);parts['joint-test-'+name]=sample
    sample.export(OUT/f'joint-test-{name}.stl')

# Keys have their own exact seated collision checks.
for y in [-176.,176.]:
    k=key.copy();k.apply_translation([0,y,10.1])  # key Z10.1..11.1, seat floor11.2
    for obstacle in [body,display]:
        h=tm.boolean.intersection([k,obstacle],engine='manifold')
        assert len(h.faces)==0 or abs(h.volume)<.01
parts['joining-key']=key
fit=tm.boolean.intersection([body,box([24,40,40],[70,174,10])],engine='manifold')
fit.apply_translation(-fit.bounds[0]);parts['display-fit-test']=fit
alignment=tm.boolean.intersection([body,box([24,40,40],[140,174,15])],engine='manifold')
alignment.apply_translation(-alignment.bounds[0]);parts['alignment-fit-test']=alignment

def components(m):
    p=list(range(len(m.vertices)))
    def root(i):
        while p[i]!=i:p[i]=p[p[i]];i=p[i]
        return i
    for a,b in m.edges:p[root(int(a))]=root(int(b))
    return len({root(i) for i in range(len(p))})
report={}
for name,m in {**parts,'assembled':body}.items():
    # STL uses float32; remove triangles collapsed by that serialization before export.
    m.vertices=m.vertices.astype(np.float32).astype(np.float64)
    m.merge_vertices(digits_vertex=7)
    m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    assert m.is_watertight and m.volume>0 and components(m)==1,name
    filename={'left':'bezel-left','right':'bezel-right','assembled':'bezel-assembled'}.get(name,name)
    m.export(OUT/f'{filename}.stl')
    assert tm.load_mesh(OUT/f'{filename}.stl').is_watertight,name
    if name in ['left','right']:
        flat=np.all(np.isclose(m.triangles[:,:,2],0,atol=1e-6),axis=1)
        bed_area=float(m.area_faces[flat].sum())
        contact=tm.Trimesh(m.vertices,m.faces[flat],process=True)
        assert bed_area>1000 and components(contact)==1,(name,bed_area)
        assert np.all(m.face_normals[flat,2]<-.99),name
        report[name+'_bed_contact']={'plane_z_mm':0,'flat_area_mm2':bed_area,
            'connected_contact_regions':1,'land_top_bottom_mm':2.2,'land_sides_mm':2.7}
    report[name]={'watertight':True,'positive_volume':True,'surface_components':1,
                  'bounds_mm':m.extents.round(4).tolist(),'volume_cm3':round(m.volume/1000,3)}
assert all(parts['left'].extents < [420,420,500])
assert np.allclose(back[-1][:,2],1)
report['design']={'inner_lip_underside_z_mm':1,'inner_lip_top_z_mm':3.4,'peak_z_mm':30,
    'shell_z_thickness_mm':SHELL,'flat_land_top_bottom_mm':2.2,'flat_land_sides_mm':2.7,'flat_land_installed_z_mm':1.,'joint_min_inner_edge_clearance_mm':7,
    'key_size_mm':[27.6,9.6,1],'key_seated_z_mm':[10.1,11.1],
    'key_to_factory_face_min_z_gap_mm':3.1,'factory_face_z_mm':7,
    'post_contact_z_mm':7.2,'adhesive_allowance_mm':.2,'post_count':12,'posts':post_report,
    'locator_count':8,'locators':locator_report,'display_intersection_mm3':0.,'print_slicing_and_physical_fit_verified':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')

fig,axs=plt.subplots(1,2,figsize=(15,7),facecolor='#f3efe5',gridspec_kw={'width_ratios':[1.5,1]})
ax=axs[0]
ax.add_patch(Rectangle((-331.45,-216.275),662.9,418.55,facecolor='#777',alpha=.4))
ax.add_patch(Rectangle((-298.45,-168.275),596.9,336.55,facecolor='#222'))
ax.add_patch(Polygon(contour(-1),facecolor='#9b9f56'))
ax.add_patch(Polygon(contour(0),facecolor='#79842d'))
ax.add_patch(Polygon(contour(1),facecolor='#222'))
for x,y in post_xy:ax.add_patch(Rectangle((x-4,y-4),8,8,facecolor='#eaad52',edgecolor='#70471a'))
for y in [-176,176]:ax.add_patch(Rectangle((-14,y-5),28,10,facecolor='#8fbee0',edgecolor='#31556f'))
for tab in locators:
    bounds=tab.bounds
    ax.add_patch(Rectangle(bounds[0,:2],*(bounds[1,:2]-bounds[0,:2]),facecolor='#e57858',edgecolor='#8e3020'))
ax.set(xlim=(-350,350),ylim=(-225,225),aspect='equal',title='REAR · orange: glue feet / red: locators / blue: keys');ax.set_axis_off()
ax=axs[1]
# Exact top-center section. Curves use the same contour functions as the mesh.
ys=[];zr=[]
for t in TS:
    xy=contour(t);i=N//4;ys.append(xy[i,1]);zr.append(rear(t,xy)[i])
ax.plot(ys,zr,color='#79842d',lw=2,label='Underside')
ax.plot(ys,[original_rear(t,contour(t))[0]+SHELL for t in TS],color='#79842d',lw=4,label='Visible face')
ym=np.array(ys);mask=(ym>=170)&(ym<=182)
ax.fill_between(ym[mask],10,(np.array(zr)+SHELL)[mask],color='#79842d',alpha=.5,label='Local rear joint pad')
ax.fill_between([168.275,202.275],[-12,-12],[7,7],color='#777',alpha=.6,label='Factory bezel')
ax.plot([150,168.275],[0,0],color='#222',lw=3,label='Glass Z0')
ax.add_patch(Rectangle((171.2,10.1),9.6,1,facecolor='#8fbee0',label='Rear bridge key'))
ax.add_patch(Rectangle((185,27),7,3,facecolor='#9b9f56',label='Peak-level flange'))
ax.annotate('1 mm air gap',xy=(163,1),xytext=(150,6),arrowprops={'arrowstyle':'->'},fontsize=10)
ax.set(xlim=(150,205),ylim=(-2,35),xlabel='Distance above screen center (mm)',ylabel='Forward from glass (mm)',title='TOP-CENTER SECTION')
ax.legend(fontsize=8,loc='upper left')
fig.suptitle('GREEN BEZEL · FLAT INNER PRINTING LAND',fontsize=19,weight='bold')
fig.tight_layout(rect=(0,0,1,.94));fig.savefig(OUT/'bezel-fit-preview.png',dpi=150);plt.close(fig)
print(json.dumps(report['design'],indent=2))
