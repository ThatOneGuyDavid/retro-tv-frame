"""Faceplate cut geometry only, plus retained tile registration marks. Units mm."""
from pathlib import Path
import math,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
from matplotlib.backends.backend_pdf import PdfPages
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
reference=json.loads((ROOT/'assembly/validation.json').read_text())
bounds=reference['parts']['wood']['bounds_mm']
LEFT,BOTTOM=bounds[0][:2]
RIGHT,TOP=bounds[1][:2]
WIDTH,HEIGHT=RIGHT-LEFT,TOP-BOTTOM
CX=392.5
GRILLE_Y=-102.
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

screen_cut=squircle(640,369)
grille_cut=rounded(100,160,8,CX,GRILLE_Y)

def drawing(ax,detail=True):
    ax.add_patch(Rectangle((LEFT,BOTTOM),WIDTH,HEIGHT,fill=False,lw=.8,color='black'))
    ax.add_patch(Polygon(screen_cut,fill=False,lw=.8,color='black'))
    ax.add_patch(Polygon(grille_cut,fill=False,lw=.8,color='black'))
    if detail:
        ax.text(-10,0,'SCREEN CUTOUT',ha='center',va='center',fontsize=9)
        ax.text(CX,GRILLE_Y,'SPEAKER CUTOUT',ha='center',va='center',fontsize=7)
        ax.text(LEFT+6,TOP-10,'TOP / FRONT VIEW',fontsize=7,va='top')
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
        'Fine crosses and dotted lines are tile alignment guides.\n'
        'Only the faceplate boundary and cutouts are shown.\n\n'
        'Panel: 803.2 × 434.75 mm; screen opening: 640 × 369 mm.\n'
        'Screen contour is curved, NOT a bounding rectangle.\n'
        'Grille opening: 100 × 160 mm, corner radius 8 mm.\n'
        'View is FRONT / TOP UP. Attach template to wood front.\n\n'
        'Dry-fit printed parts before cutting final material.\n'
        '1/8 inch wood shown in assembly; thinner is possible.\n'
        'Check against the actual prints before cutting wood.')
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



assert np.isclose(WIDTH,803.2,atol=.0001) and np.isclose(HEIGHT,434.75,atol=.0001)
assert np.isclose(TW/7.5,25.4) and np.isclose(TH/10,25.4)
assert LEFT+(COLS-1)*SX+TW>=RIGHT and TOP-(ROWS-1)*SY-TH<=BOTTOM
fig,ax=plt.subplots(figsize=(13,8))
drawing(ax);ax.set(xlim=(LEFT-8,RIGHT+8),ylim=(BOTTOM-8,TOP+8),aspect='equal');ax.set_axis_off()
fig.tight_layout();fig.savefig(OUT/'faceplate-preview.png',dpi=140);plt.close(fig)
report={'panel_size_mm':[WIDTH,HEIGHT],'closed_cut_contours':3,'other_layer_outlines':0,'shaft_guides':0,'page_inches':[8.5,11],'pdf_pages':1+len(tiles),'columns':COLS,'rows':ROWS,'overlap_mm':10,'print_margin_mm':MARGIN,'scale_mm_per_inch':[TW/7.5,TH/10],'tiles':tiles,'source':'assembly/validation.json'}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='tiles'},indent=2))
