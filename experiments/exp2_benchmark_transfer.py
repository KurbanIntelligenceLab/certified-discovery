"""EXP-2 (R2.1): does a model's benchmark precision on the whole WBM corpus transfer to a new pool?
WBM was generated in five successive element-substitution rounds (material_id 'wbm-<step>-<k>').
Treat each round as a separate screening campaign: compare the precision the model's full-WBM benchmark
census would imply with the round's own census precision, and with the half-width a 500-label
certification of that round would achieve (Corollary 1 at the round's census precision and its own
margin correlation; the classical label-only half-width is also reported)."""
import numpy as np, pandas as pd
from wbm_data import load, campaign
wbm, EP = load(); z = 1.959963984540054; rows = []
step = wbm.index.str.split("-").str[1].astype(int)
for m in EP:
    idx, y, f = campaign(wbm, EP[m], 0.0)
    s = step[wbm.index.get_indexer(idx)]; pi_bench = y.mean()
    for k in sorted(set(s)):
        yk, fk = y[s == k], f[s == k]; N = len(yk); pk = yk.mean()
        Sy2 = pk * (1 - pk) * N / (N - 1); rho = np.corrcoef(yk, fk)[0, 1]
        hw_c = z * np.sqrt(Sy2 * (1 / 500 - 1 / N)); hw = z * np.sqrt((1 - rho**2) * Sy2 * (1 / 500 - 1 / N))
        rows.append(dict(model=m, wbm_round=k, N=N, census_precision=pk, benchmark_precision=pi_bench,
                         transfer_error_pp=100 * (pi_bench - pk), count_error=round((pi_bench - pk) * N), rho=rho,
                         halfwidth_classical_pp=100 * hw_c, halfwidth_n500_pp=100 * hw, exceeds_halfwidth=abs(pi_bench - pk) > hw))
d = pd.DataFrame(rows); d.to_csv("results/exp2_benchmark_transfer.csv", index=False)
g = d.groupby("model").agg(prec_min=("census_precision", "min"), prec_max=("census_precision", "max"),
                           max_abs_err_pp=("transfer_error_pp", lambda x: x.abs().max()),
                           rounds_beyond_hw=("exceeds_halfwidth", "sum"))
print(g.round(3).to_string())
print(f"rounds where benchmark precision misses the round's census by more than the n=500 half-width: "
      f"{int(d.exceeds_halfwidth.sum())}/{len(d)}; max |error| {d.transfer_error_pp.abs().max():.1f} pp, "
      f"max count error {d.count_error.abs().max():,} materials")

# Second split: chemical arity (a campaign restricted to binaries, ternaries, or quaternaries+).
import re
nel = wbm["formula"].map(lambda s: len(set(re.findall(r"[A-Z][a-z]?", str(s))))).to_numpy()
rows = []
for m in EP:
    idx, y, f = campaign(wbm, EP[m], 0.0); pi_bench = y.mean()
    a = np.clip(nel[wbm.index.get_indexer(idx)], 2, 4)
    for k in (2, 3, 4):
        yk, fk = y[a == k], f[a == k]; N = len(yk)
        if N < 1000: continue
        pk = yk.mean(); Sy2 = pk * (1 - pk) * N / (N - 1); rho = np.corrcoef(yk, fk)[0, 1]
        hw_c = z * np.sqrt(Sy2 * (1 / 500 - 1 / N)); hw = z * np.sqrt((1 - rho**2) * Sy2 * (1 / 500 - 1 / N))
        rows.append(dict(model=m, arity={2: "binary", 3: "ternary", 4: "quaternary+"}[k], N=N,
                         census_precision=pk, benchmark_precision=pi_bench, transfer_error_pp=100 * (pi_bench - pk),
                         count_error=round((pi_bench - pk) * N), rho=rho, halfwidth_classical_pp=100 * hw_c,
                         halfwidth_n500_pp=100 * hw, exceeds_halfwidth=abs(pi_bench - pk) > hw))
a = pd.DataFrame(rows); a.to_csv("results/exp2_benchmark_transfer_arity.csv", index=False)
print(a[["model", "arity", "N", "census_precision", "transfer_error_pp", "halfwidth_n500_pp"]].round(3).to_string(index=False))
print(f"arity pools beyond n=500 half-width: {int(a.exceeds_halfwidth.sum())}/{len(a)}; "
      f"max |error| {a.transfer_error_pp.abs().max():.1f} pp, max count error {a.count_error.abs().max():,}")
