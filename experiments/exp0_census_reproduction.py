"""EXP-0: independent reproduction of the Table 1 census columns (flagged, true) for the five
earlier-generation models from the pinned public files, compared with table1_raw.csv."""
import pandas as pd, sys
from wbm_data import load, campaign
wbm, EP = load()
t1 = pd.read_csv("../results/table1_raw.csv")
rows, bad = [], 0
for m in EP:
    for pool in ("full", "uniq_protos"):
        for tau in (0.0, 0.05, 0.1):
            idx, y, f = campaign(wbm, EP[m], tau, uniq=(pool == "uniq_protos"))
            ref = t1[(t1.model == m) & (t1.pool == pool) & (t1.tau == tau)].iloc[0]
            ok = len(y) == ref.flagged and int(y.sum()) == ref["true"]
            bad += not ok
            rows.append(dict(model=m, pool=pool, tau=tau, flagged=len(y), true=int(y.sum()),
                             paper_flagged=int(ref.flagged), paper_true=int(ref["true"]), match=ok))
out = pd.DataFrame(rows); out.to_csv("results/exp0_census_reproduction.csv", index=False)
mae = {m: float((EP[m] - wbm["e_above_hull_mp2020_corrected_ppd_mp"]).abs().mean()) for m in EP}
ref_mae = pd.read_csv("../results/model_mae.csv").set_index("model").mae_eV_per_atom
print(f"census configs matching paper: {len(out) - bad}/{len(out)}")
print("MAE abs diff vs model_mae.csv:", {m: f"{abs(mae[m] - ref_mae[m]):.2e}" for m in mae})
sys.exit(1 if bad else 0)
