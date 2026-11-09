"""Rebuild the current design in dependency order. Does not need network access."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
for name in ['display','knobs','grille','bezel','assembly','faceplate']:
    print('Building '+name,flush=True)
    subprocess.run([sys.executable,str(ROOT/'design'/name/'build.py')],check=True,cwd=ROOT)
