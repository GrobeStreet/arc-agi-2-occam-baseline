"""ARC-AGI-2 program-synthesis solver v2 (CPU-only, deterministic, no network).

Same contract as dsl.py: build_programs(train_pairs) -> [(name, fn)], passes_demos,
complexity(name). v2 ENRICHES the program space (more parameter-free primitives,
a bounded depth-3 layer, more derived parameterized ops) so that MORE
demonstration-consistent programs exist per task. The point is NOT to solve more
tasks: it is to over-generate candidates that agree on the demonstrations yet may
disagree on the held-out grid -- i.e. to populate the calibration curve and the
program-selection (ambiguity) analysis with a much larger, more consequential base,
exactly as the paper's limitations section anticipates a richer solver would.

complexity(name) remains a description-length proxy: number of composed ops (depth)
plus 1 if any op carries derived parameters. Shorter == simpler == the Occam pick.
"""
import numpy as np
from itertools import product
from scipy import ndimage

# ---------- parameter-free geometry ----------
def _id(g): return g
def _r90(g): return np.rot90(g, 1)
def _r180(g): return np.rot90(g, 2)
def _r270(g): return np.rot90(g, 3)
def _fh(g): return np.fliplr(g)
def _fv(g): return np.flipud(g)
def _tp(g): return g.T
def _atp(g): return np.rot90(np.fliplr(g), 1)
GEOM = {"id": _id, "rot90": _r90, "rot180": _r180, "rot270": _r270,
        "flipH": _fh, "flipV": _fv, "transpose": _tp, "antitranspose": _atp}

def _bg(g):
    v, c = np.unique(g, return_counts=True); return int(v[np.argmax(c)])

# ---------- shape / structure ----------
def _crop(g):
    nz = np.argwhere(g != 0)
    if nz.size == 0: return None
    (r0, c0), (r1, c1) = nz.min(0), nz.max(0) + 1; return g[r0:r1, c0:c1]
def _crop_bg(g):
    b = _bg(g); nz = np.argwhere(g != b)
    if nz.size == 0: return None
    (r0, c0), (r1, c1) = nz.min(0), nz.max(0) + 1; return g[r0:r1, c0:c1]
def _gravD(g):
    o = np.zeros_like(g)
    for c in range(g.shape[1]):
        v = g[:, c][g[:, c] != 0]
        if len(v): o[g.shape[0] - len(v):, c] = v
    return o
def _gravU(g):
    o = np.zeros_like(g)
    for c in range(g.shape[1]):
        v = g[:, c][g[:, c] != 0]
        if len(v): o[:len(v), c] = v
    return o
def _gravL(g):
    o = np.zeros_like(g)
    for r in range(g.shape[0]):
        v = g[r, :][g[r, :] != 0]
        if len(v): o[r, :len(v)] = v
    return o
def _gravR(g):
    o = np.zeros_like(g)
    for r in range(g.shape[0]):
        v = g[r, :][g[r, :] != 0]
        if len(v): o[r, g.shape[1] - len(v):] = v
    return o
def _mirrorLR(g): return np.concatenate([g, np.fliplr(g)], 1)
def _mirrorUD(g): return np.concatenate([g, np.flipud(g)], 0)
def _mirrorLR_r(g): return np.concatenate([np.fliplr(g), g], 1)
def _mirrorUD_r(g): return np.concatenate([np.flipud(g), g], 0)
def _symOR(g):
    out = g.copy()
    for t in (np.fliplr(g), np.flipud(g), np.rot90(g, 2)):
        if t.shape == out.shape: out = np.where(out == 0, t, out)
    return out
def _symOR4(g):
    """4-fold symmetrize including transpose (square grids)."""
    if g.shape[0] != g.shape[1]: return None
    out = g.copy()
    for t in (np.fliplr(g), np.flipud(g), np.rot90(g, 1), np.rot90(g, 2),
              np.rot90(g, 3), g.T, np.rot90(np.fliplr(g), 1)):
        if t.shape == out.shape: out = np.where(out == 0, t, out)
    return out
def _trim(g):
    """remove a uniform 1-cell border if present."""
    if g.shape[0] < 3 or g.shape[1] < 3: return None
    return g[1:-1, 1:-1]
def _dedup_rows_cols(g):
    """collapse consecutive duplicate rows and columns (grid 'compression')."""
    if g.shape[0] < 2 and g.shape[1] < 2: return None
    keep_r = [0] + [i for i in range(1, g.shape[0]) if not np.array_equal(g[i], g[i - 1])]
    h = g[keep_r]
    keep_c = [0] + [j for j in range(1, h.shape[1]) if not np.array_equal(h[:, j], h[:, j - 1])]
    o = h[:, keep_c]
    return o if o.shape != g.shape else None
def _unique_rows_cols(g):
    """keep first occurrence of each distinct row, then each distinct col."""
    seen = []; idx = []
    for i in range(g.shape[0]):
        key = g[i].tobytes()
        if key not in seen: seen.append(key); idx.append(i)
    h = g[idx]; seen = []; jdx = []
    for j in range(h.shape[1]):
        key = h[:, j].tobytes()
        if key not in seen: seen.append(key); jdx.append(j)
    o = h[:, jdx]
    return o if o.shape != g.shape else None
def _half_top(g): return g[:g.shape[0] // 2, :] if g.shape[0] >= 2 else None
def _half_bottom(g): return g[(g.shape[0] + 1) // 2:, :] if g.shape[0] >= 2 else None
def _half_left(g): return g[:, :g.shape[1] // 2] if g.shape[1] >= 2 else None
def _half_right(g): return g[:, (g.shape[1] + 1) // 2:] if g.shape[1] >= 2 else None
SHAPE = {"crop": _crop, "cropBg": _crop_bg,
         "gravityDown": _gravD, "gravityUp": _gravU, "gravityLeft": _gravL, "gravityRight": _gravR,
         "mirrorLR": _mirrorLR, "mirrorUD": _mirrorUD, "mirrorLRr": _mirrorLR_r, "mirrorUDr": _mirrorUD_r,
         "symOR": _symOR, "symOR4": _symOR4, "trim": _trim,
         "dedupRC": _dedup_rows_cols, "uniqueRC": _unique_rows_cols,
         "halfTop": _half_top, "halfBottom": _half_bottom, "halfLeft": _half_left, "halfRight": _half_right}

# ---------- object (connected component) ops ----------
def _components(g, bg):
    m = (g != bg).astype(int)
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    return lab, n
def _keep_largest(g):
    b = _bg(g); lab, n = _components(g, b)
    if n == 0: return None
    sizes = [(lab == i).sum() for i in range(1, n + 1)]
    big = 1 + int(np.argmax(sizes)); o = np.full_like(g, b); o[lab == big] = g[lab == big]; return o
def _keep_smallest(g):
    b = _bg(g); lab, n = _components(g, b)
    if n == 0: return None
    sizes = [(lab == i).sum() for i in range(1, n + 1)]
    sm = 1 + int(np.argmin(sizes)); o = np.full_like(g, b); o[lab == sm] = g[lab == sm]; return o
def _remove_largest(g):
    b = _bg(g); lab, n = _components(g, b)
    if n == 0: return None
    sizes = [(lab == i).sum() for i in range(1, n + 1)]
    big = 1 + int(np.argmax(sizes)); o = g.copy(); o[lab == big] = b; return o
def _crop_largest(g):
    b = _bg(g); lab, n = _components(g, b)
    if n == 0: return None
    sizes = [(lab == i).sum() for i in range(1, n + 1)]
    big = 1 + int(np.argmax(sizes)); nz = np.argwhere(lab == big)
    (r0, c0), (r1, c1) = nz.min(0), nz.max(0) + 1; return g[r0:r1, c0:c1]
def _crop_smallest(g):
    b = _bg(g); lab, n = _components(g, b)
    if n == 0: return None
    sizes = [(lab == i).sum() for i in range(1, n + 1)]
    sm = 1 + int(np.argmin(sizes)); nz = np.argwhere(lab == sm)
    (r0, c0), (r1, c1) = nz.min(0), nz.max(0) + 1; return g[r0:r1, c0:c1]
OBJ = {"keepLargest": _keep_largest, "keepSmallest": _keep_smallest,
       "removeLargest": _remove_largest, "cropLargest": _crop_largest, "cropSmallest": _crop_smallest}

# ---------- color ops (parameter-free, derived from the grid itself) ----------
def _most_common_fg_only(g):
    b = _bg(g); vals = g[g != b]
    if vals.size == 0: return None
    v, c = np.unique(vals, return_counts=True); keep = int(v[np.argmax(c)])
    o = np.full_like(g, b); o[g == keep] = keep; return o
def _least_common_fg_only(g):
    b = _bg(g); vals = g[g != b]
    if vals.size == 0: return None
    v, c = np.unique(vals, return_counts=True); keep = int(v[np.argmin(c)])
    o = np.full_like(g, b); o[g == keep] = keep; return o
def _binarize(g):
    b = _bg(g); o = np.zeros_like(g); o[g != b] = 1; return o
COLOR = {"mostCommonFg": _most_common_fg_only, "leastCommonFg": _least_common_fg_only,
         "binarize": _binarize}

# ---------- fractal tiling ----------
def _fractal_factory(transform, on_nonzero=True):
    def f(g):
        b = _bg(g); h, w = g.shape; o = np.full((h * h, w * w), b, dtype=g.dtype)
        t = transform(g)
        if t.shape != g.shape: return None
        for i in range(h):
            for j in range(w):
                cond = (g[i, j] != b) if on_nonzero else (g[i, j] == b)
                if cond: o[i * h:(i + 1) * h, j * w:(j + 1) * w] = t
        return o
    return f

# ---------- half-combine (split by center, logical op) ----------
def _split_halves(g):
    h, w = g.shape; outs = []
    if w % 2 == 1: c = w // 2; outs.append((g[:, :c], g[:, c + 1:]))
    if w % 2 == 0: outs.append((g[:, :w // 2], g[:, w // 2:]))
    if h % 2 == 1: r = h // 2; outs.append((g[:r, :], g[r + 1:, :]))
    if h % 2 == 0: outs.append((g[:h // 2, :], g[h // 2:, :]))
    return outs
def _halfcombine_factory(op, fill):
    def f(g):
        for A, B in _split_halves(g):
            if A.shape != B.shape or A.size == 0: continue
            a = (A != _bg(g)); b = (B != _bg(g))
            if op == "AND": m = a & b
            elif op == "OR": m = a | b
            elif op == "XOR": m = a ^ b
            elif op == "DIFF": m = a & ~b
            elif op == "NAND": m = ~(a & b)
            else: return None
            return np.where(m, fill, 0).astype(g.dtype)
        return None
    return f

# ---------- derived parameterized ----------
def derive_color_map(pairs):
    m = {}
    for i, o in pairs:
        if i.shape != o.shape: return None
        for a, b in zip(i.flatten(), o.flatten()):
            if a in m and m[a] != b: return None
            m[a] = b
    return m
def _apply_cm(g, m):
    o = g.copy()
    for a, b in m.items(): o[g == a] = b
    return o
def derive_ratio(pairs, kind):
    s = set()
    for i, o in pairs:
        if kind in ("tile", "scale"):
            if o.shape[0] % i.shape[0] or o.shape[1] % i.shape[1]: return None
            s.add((o.shape[0] // i.shape[0], o.shape[1] // i.shape[1]))
        elif kind == "reduce":
            if i.shape[0] % o.shape[0] or i.shape[1] % o.shape[1]: return None
            s.add((i.shape[0] // o.shape[0], i.shape[1] // o.shape[1]))
    return s.pop() if len(s) == 1 else None
def _tile(g, f): return np.tile(g, f)
def _scale(g, k): return np.kron(g, np.ones(k, dtype=g.dtype))
def _reduce(g, k):
    kh, kw = k
    if g.shape[0] % kh or g.shape[1] % kw: return None
    return g[::kh, ::kw]
def derive_const_output(pairs):
    """if every demo maps to the SAME output grid, that constant is a candidate."""
    outs = [o for _, o in pairs]
    first = outs[0]
    for o in outs[1:]:
        if o.shape != first.shape or not np.array_equal(o, first): return None
    return first

def _ok(x): return isinstance(x, np.ndarray) and x.size > 0

def build_programs(train_pairs):
    progs = []
    base = list(GEOM.items()) + list(SHAPE.items()) + list(OBJ.items()) + list(COLOR.items())
    for n, f in base: progs.append((n, f))
    # depth-2: (geom) then (any base)
    for (n1, f1), (n2, f2) in product(GEOM.items(), base):
        if n1 == "id" or n2 == "id": continue
        progs.append((f"{n2}∘{n1}",
                      (lambda a, b: (lambda g: (b(a(g)) if _ok(a(g)) else None)))(f1, f2)))
    # depth-3 (bounded): (geom) then (geom) then a small high-yield struct set.
    # Bounded to keep the enumeration finite/fast while still over-generating candidates.
    _d3 = {"crop", "cropBg", "keepLargest", "cropLargest", "symOR", "trim", "gravityDown"}
    struct = [(n, f) for n, f in (list(SHAPE.items()) + list(OBJ.items())) if n in _d3]
    for (n1, f1), (n2, f2) in product(GEOM.items(), GEOM.items()):
        if n1 == "id" or n2 == "id" or n1 == n2: continue
        for (n3, f3) in struct:
            progs.append((f"{n3}∘{n2}∘{n1}",
                          (lambda a, b, c: (lambda g: (c(b(a(g))) if (_ok(a(g)) and _ok(b(a(g)))) else None)))(f1, f2, f3)))
    # fractal tiling variants
    for tn, tf in list(GEOM.items()):
        progs.append((f"fractal[{tn}]", _fractal_factory(tf, True)))
        progs.append((f"fractalInv[{tn}]", _fractal_factory(tf, False)))
    # half-combine
    for op in ("AND", "OR", "XOR", "DIFF", "NAND"):
        for fill in range(1, 10):
            progs.append((f"half{op}:{fill}", _halfcombine_factory(op, fill)))
    # derived: color map (+ composed with a geometry)
    cm = derive_color_map(train_pairs)
    if cm and any(a != b for a, b in cm.items()):
        progs.append(("colorMap", lambda g, m=cm: _apply_cm(g, m)))
        for n, f in GEOM.items():
            if n == "id": continue
            progs.append((f"colorMap∘{n}", lambda g, f=f, m=cm: _apply_cm(f(g), m)))
    # derived: tile / scale / reduce ratios
    for kind, ap in (("tile", _tile), ("scale", _scale)):
        r = derive_ratio(train_pairs, kind)
        if r and r != (1, 1): progs.append((f"{kind}{r}", lambda g, k=r, ap=ap: ap(g, k)))
    rr = derive_ratio(train_pairs, "reduce")
    if rr and rr != (1, 1): progs.append((f"reduce{rr}", lambda g, k=rr: _reduce(g, k)))
    # NOTE: a "constant output" hypothesis (memorize the output grid) trivially fits
    # any SINGLE demonstration and never generalizes; including it would inflate the
    # k=1 miscalibration with a degenerate non-transformation. We deliberately exclude
    # it so the calibration curve measures genuine transformation hypotheses only.
    return progs

def passes_demos(fn, pairs):
    for i, o in pairs:
        try: p = fn(i)
        except Exception: return False
        if not _ok(p) or p.shape != o.shape or not np.array_equal(p, o): return False
    return True

def complexity(name):
    """description-length proxy: composed-op count (depth) + 1 if parameterized."""
    depth = name.count("∘") + 1
    param = 1 if any(k in name for k in
                     ("colorMap", "tile", "scale", "reduce", "fractal", "half", "constOut")) else 0
    return depth + param
