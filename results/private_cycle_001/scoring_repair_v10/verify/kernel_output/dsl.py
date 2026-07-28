"""ARC-AGI-2 program-synthesis solver (CPU-only, deterministic, no network).
Enumerates candidate programs; a program 'passes demos' iff it reproduces EVERY
demonstration output exactly. Richer program space -> more demo-consistent programs
that may DISAGREE on the test output (the program-selection problem we study)."""
import numpy as np
from itertools import product
from scipy import ndimage

# ---------- parameter-free geom ----------
def _id(g): return g
def _r90(g): return np.rot90(g,1)
def _r180(g): return np.rot90(g,2)
def _r270(g): return np.rot90(g,3)
def _fh(g): return np.fliplr(g)
def _fv(g): return np.flipud(g)
def _tp(g): return g.T
def _atp(g): return np.rot90(np.fliplr(g),1)
GEOM = {"id":_id,"rot90":_r90,"rot180":_r180,"rot270":_r270,
        "flipH":_fh,"flipV":_fv,"transpose":_tp,"antitranspose":_atp}

def _bg(g):
    v,c=np.unique(g,return_counts=True); return int(v[np.argmax(c)])
def _crop(g):
    nz=np.argwhere(g!=0)
    if nz.size==0: return None
    (r0,c0),(r1,c1)=nz.min(0),nz.max(0)+1; return g[r0:r1,c0:c1]
def _crop_bg(g):
    b=_bg(g); nz=np.argwhere(g!=b)
    if nz.size==0: return None
    (r0,c0),(r1,c1)=nz.min(0),nz.max(0)+1; return g[r0:r1,c0:c1]
def _gravD(g):
    o=np.zeros_like(g)
    for c in range(g.shape[1]):
        v=g[:,c][g[:,c]!=0]
        if len(v): o[g.shape[0]-len(v):,c]=v
    return o
def _mirrorLR(g): return np.concatenate([g,np.fliplr(g)],1)
def _mirrorUD(g): return np.concatenate([g,np.flipud(g)],0)
def _mirrorLR_r(g): return np.concatenate([np.fliplr(g),g],1)
def _symOR(g):
    """make 4-fold symmetric by OR-ing flips (nonzero wins)."""
    out=g.copy()
    for t in (np.fliplr(g),np.flipud(g),np.rot90(g,2)):
        if t.shape==out.shape: out=np.where(out==0,t,out)
    return out
SHAPE={"crop":_crop,"cropBg":_crop_bg,"gravityDown":_gravD,
       "mirrorLR":_mirrorLR,"mirrorUD":_mirrorUD,"mirrorLRr":_mirrorLR_r,"symOR":_symOR}

# ---------- object (connected component) ops ----------
def _components(g,bg):
    m=(g!=bg).astype(int)
    lab,n=ndimage.label(m,structure=np.ones((3,3)))
    return lab,n
def _keep_largest(g):
    b=_bg(g); lab,n=_components(g,b)
    if n==0: return None
    sizes=[(lab==i).sum() for i in range(1,n+1)]
    big=1+int(np.argmax(sizes)); o=np.full_like(g,b); o[lab==big]=g[lab==big]; return o
def _remove_largest(g):
    b=_bg(g); lab,n=_components(g,b)
    if n==0: return None
    sizes=[(lab==i).sum() for i in range(1,n+1)]
    big=1+int(np.argmax(sizes)); o=g.copy(); o[lab==big]=b; return o
def _crop_largest(g):
    b=_bg(g); lab,n=_components(g,b)
    if n==0: return None
    sizes=[(lab==i).sum() for i in range(1,n+1)]
    big=1+int(np.argmax(sizes)); nz=np.argwhere(lab==big)
    (r0,c0),(r1,c1)=nz.min(0),nz.max(0)+1; return g[r0:r1,c0:c1]
OBJ={"keepLargest":_keep_largest,"removeLargest":_remove_largest,"cropLargest":_crop_largest}

# ---------- fractal tiling (very common ARC) ----------
def _fractal_factory(transform, on_nonzero=True):
    def f(g):
        b=_bg(g); h,w=g.shape; o=np.full((h*h,w*w),b,dtype=g.dtype)
        t=transform(g)
        if t.shape!=g.shape: return None
        for i in range(h):
            for j in range(w):
                cond = (g[i,j]!=b) if on_nonzero else (g[i,j]==b)
                if cond: o[i*h:(i+1)*h, j*w:(j+1)*w]=t
        return o
    return f

# ---------- half-combine (split by center, logical op) ----------
def _split_halves(g):
    h,w=g.shape
    outs=[]
    if w%2==1:  # vertical separator col
        c=w//2; outs.append((g[:,:c],g[:,c+1:]))
    if w%2==0:
        outs.append((g[:,:w//2],g[:,w//2:]))
    if h%2==1:
        r=h//2; outs.append((g[:r,:],g[r+1:,:]))
    if h%2==0:
        outs.append((g[:h//2,:],g[h//2:,:]))
    return outs
def _halfcombine_factory(op, fill):
    def f(g):
        for A,B in _split_halves(g):
            if A.shape!=B.shape or A.size==0: continue
            a=(A!=_bg(g)); b=(B!=_bg(g))
            if op=="AND": m=a&b
            elif op=="OR": m=a|b
            elif op=="XOR": m=a^b
            elif op=="DIFF": m=a&~b
            else: return None
            return np.where(m,fill,0).astype(g.dtype)
        return None
    return f

# ---------- derived parameterized ----------
def derive_color_map(pairs):
    m={}
    for i,o in pairs:
        if i.shape!=o.shape: return None
        for a,b in zip(i.flatten(),o.flatten()):
            if a in m and m[a]!=b: return None
            m[a]=b
    return m
def _apply_cm(g,m):
    o=g.copy()
    for a,b in m.items(): o[g==a]=b
    return o
def derive_ratio(pairs,kind):
    s=set()
    for i,o in pairs:
        if kind=="tile" or kind=="scale":
            if o.shape[0]%i.shape[0] or o.shape[1]%i.shape[1]: return None
            s.add((o.shape[0]//i.shape[0],o.shape[1]//i.shape[1]))
        elif kind=="reduce":
            if i.shape[0]%o.shape[0] or i.shape[1]%o.shape[1]: return None
            s.add((i.shape[0]//o.shape[0],i.shape[1]//o.shape[1]))
    return s.pop() if len(s)==1 else None
def _tile(g,f): return np.tile(g,f)
def _scale(g,k): return np.kron(g,np.ones(k,dtype=g.dtype))
def _reduce(g,k):
    kh,kw=k
    if g.shape[0]%kh or g.shape[1]%kw: return None
    o=g[::kh,::kw]; return o

def build_programs(train_pairs):
    progs=[]
    base=list(GEOM.items())+list(SHAPE.items())+list(OBJ.items())
    for n,f in base: progs.append((n,f))
    # depth-2: geom then (geom|shape|obj)
    for (n1,f1),(n2,f2) in product(GEOM.items(),base):
        if n1=="id" or n2=="id": continue
        progs.append((f"{n2}∘{n1}",(lambda a,b:(lambda g:(b(a(g)) if _ok(a(g)) else None)))(f1,f2)))
    # fractal tiling variants
    for tn,tf in list(GEOM.items()):
        progs.append((f"fractal[{tn}]",_fractal_factory(tf,True)))
        progs.append((f"fractalInv[{tn}]",_fractal_factory(tf,False)))
    # half-combine
    for op in ("AND","OR","XOR","DIFF"):
        for fill in range(1,10):
            progs.append((f"half{op}:{fill}",_halfcombine_factory(op,fill)))
    # derived
    cm=derive_color_map(train_pairs)
    if cm and any(a!=b for a,b in cm.items()):
        progs.append(("colorMap",lambda g,m=cm:_apply_cm(g,m)))
        for n,f in GEOM.items():
            if n=="id": continue
            progs.append((f"colorMap∘{n}",lambda g,f=f,m=cm:_apply_cm(f(g),m)))
    for kind,ap in (("tile",_tile),("scale",_scale)):
        r=derive_ratio(train_pairs,kind)
        if r and r!=(1,1): progs.append((f"{kind}{r}",lambda g,k=r,ap=ap:ap(g,k)))
    rr=derive_ratio(train_pairs,"reduce")
    if rr and rr!=(1,1): progs.append((f"reduce{rr}",lambda g,k=rr:_reduce(g,k)))
    return progs

def _ok(x): return isinstance(x,np.ndarray) and x.size>0

def passes_demos(fn,pairs):
    for i,o in pairs:
        try: p=fn(i)
        except Exception: return False
        if not _ok(p) or p.shape!=o.shape or not np.array_equal(p,o): return False
    return True

def complexity(name):
    depth=name.count("∘")+1
    param=1 if any(k in name for k in ("colorMap","tile","scale","reduce","fractal","half")) else 0
    return depth+param
