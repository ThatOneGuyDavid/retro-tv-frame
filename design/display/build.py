"""Generic square-edged display envelope; no manufacturer or model identity."""
from pathlib import Path
import json
import trimesh as tm

OUT=Path(__file__).resolve().parent
VIEW_W,VIEW_H=596.9,336.55
LEFT,RIGHT,TOP,BOTTOM=33.,33.,34.,48.
DEPTH,RECESS=44.,7.

def box(size,center):
    m=tm.creation.box(size);m.apply_translation(center);return m

w,h=VIEW_W+LEFT+RIGHT,VIEW_H+TOP+BOTTOM
cx,cy=(RIGHT-LEFT)/2,(TOP-BOTTOM)/2
housing=box([w,h,DEPTH],[cx,cy,RECESS-DEPTH/2])
# Single stepped solid: recess terminates exactly at the viewing surface Z0.
cut=box([VIEW_W,VIEW_H,RECESS+1],[0,0,(RECESS+1)/2])
display=tm.boolean.difference([housing,cut],engine='manifold')
assert display.is_watertight and display.volume>0
display.export(OUT/'display-reference.stl')
(OUT/'dimensions.json').write_text(json.dumps({'viewing_area_mm':[VIEW_W,VIEW_H],
    'bezel_widths_mm':{'left':LEFT,'right':RIGHT,'top':TOP,'bottom':BOTTOM},
    'outer_size_mm':[w,h,DEPTH],'glass_z_mm':0,'factory_front_z_mm':RECESS,
    'back_z_mm':RECESS-DEPTH,'square_edges_assumed':True},indent=2)+'\n')
