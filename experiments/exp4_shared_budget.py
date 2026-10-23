"""EXP-4 (R1.4; corrects the 'single budget' claim): one shared verification sample drawn from the union of
several models' flagged pools certifies all their pairwise discovery-count differences at once.
Run here for the five earlier-generation models (public files reachable from this environment); the same
script runs unchanged on the 15-model set when given the frontier prediction files (see wbm_data.FILES).
Per replicate: Holm correction across the adjacent pairs of that replicate (a real campaign's analysis).
Designs compared at equal total budget: shared sample from the K-model union vs. budget split evenly
across pair-specific unions; plus the Table 2 design (n labels per pair, (K-1)n total)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "../src")
from certdisc.core import ppi_yield_diff_ci
from wbm_data import load, TRUTH
Z = 1.959963984540054; R = 1000
import os
MODE = os.environ.get("MODELS", "five"); SUF = "_15models" if MODE == "all" else ""
wbm, EP = load(MODE)
mae = pd.read_csv("../results/model_mae.csv").set_index("model").mae_eV_per_atom
order = sorted(EP, key=mae.get); pairs = list(zip(order[:-1], order[1:]))
ok = wbm[TRUTH].notna().to_numpy().copy()
for m in order: ok &= EP[m].notna().to_numpy()
y = (wbm[TRUTH].to_numpy() <= 0)[ok].astype(float)
F = {m: (EP[m].to_numpy()[ok] <= 0).astype(float) for m in order}
U = np.zeros(len(y), bool)
for m in order: U |= F[m] > 0
yU, FU, M = y[U], {m: F[m][U] for m in order}, int(U.sum())
true_dcount = {(A, B): int((yU * FU[A]).sum() - (yU * FU[B]).sum()) for A, B in pairs}

def holm_reject(p, alpha=0.05):
    p = np.asarray(p); o = np.argsort(p); rej = np.zeros(len(p), bool)
    for r, i in enumerate(o):
        if p[i] <= alpha / (len(p) - r): rej[i] = True
        else: break
    return rej

from math import erf, sqrt
def run(design, n):
    rng = np.random.default_rng({"shared": 101, "split": 202, "perpair": 303}[design] + n)
    cover = np.zeros(len(pairs)); rej = np.zeros(len(pairs)); right = np.zeros(len(pairs)); width = np.zeros(len(pairs))
    for _ in range(R):
        res = []
        if design == "shared":
            idx = rng.choice(M, n, replace=False)
        for A, B in pairs:
            if design == "shared":
                ya, fa, fb, scale, li = yU, FU[A], FU[B], M, idx
            else:
                u = (FU[A] + FU[B]) > 0; ya, fa, fb = yU[u], FU[A][u], FU[B][u]; scale = int(u.sum())
                li = rng.choice(scale, n // len(pairs) if design == "split" else n, replace=False)
            ci = ppi_yield_diff_ci(ya[li], fa[li], fb[li], fa, fb); se = (ci.upper - ci.lower) / (2 * Z)
            p = 2 * (1 - 0.5 * (1 + erf(abs(ci.estimate) / max(se, 1e-15) / sqrt(2))))
            res.append((ci.estimate * scale, ci.lower * scale, ci.upper * scale, p))
        r = holm_reject([x[3] for x in res])
        for j, (A, B) in enumerate(pairs):
            t = true_dcount[(A, B)]; e, lo, hi, _ = res[j]
            cover[j] += lo <= t <= hi; rej[j] += r[j]; right[j] += r[j] and np.sign(e) == np.sign(t); width[j] += hi - lo
    labels = n if design == "shared" else (n if design == "split" else n * len(pairs))
    return [dict(design=design, total_labels=labels, pair=f"{A} vs {B}", true_count_diff=true_dcount[(A, B)],
                 coverage=cover[j] / R, holm_power=rej[j] / R, holm_power_correct_sign=right[j] / R,
                 mean_ci_width_count=width[j] / R) for j, (A, B) in enumerate(pairs)]

rows = []
for design, n in (("shared", 500), ("split", 500), ("perpair", 500), ("shared", 2000), ("split", 2000)):
    rows += run(design, n)
d = pd.DataFrame(rows); d.to_csv(f"results/exp4_shared_budget{SUF}.csv", index=False)
print(f"union pool of {len(order)} models: M = {M:,}; replicates = {R}")
print(d.pivot_table(index="pair", columns=["design", "total_labels"], values="holm_power").round(3).to_string())
print(d.pivot_table(index="pair", columns=["design", "total_labels"], values="coverage").round(3).to_string())
print("min coverage across all designs and pairs: %.3f" % d.coverage.min())
