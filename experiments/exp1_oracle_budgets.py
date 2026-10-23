"""Oracle Corollary-1 budgets from census quantities already in the source data (no new data).
S_y^2 = pi(1-pi) N/(N-1) for binary labels; S_r^2(lambda*) = (1-rho^2) S_y^2."""
import pandas as pd, math
D = "../results/"
t1 = pd.read_csv(D+"table1_raw.csv"); bs = pd.read_csv(D+"budgets_summary.csv").set_index("model")
f0 = t1[(t1.pool=="full")&(t1.tau==0)].set_index("model")
z = 1.959963984540054
def nstar(S2, N, w): return min(max(math.ceil(N*z*z*S2/(N*w*w+z*z*S2)), 2), N)
rows = []
for m, r in f0.iterrows():
    N, pi = int(r.flagged), r["true"]/r.flagged; rho = bs.loc[m, "rho_pool"]
    Sy2 = pi*(1-pi)*N/(N-1); Sr2 = (1-rho**2)*Sy2
    hw500_cls = z*math.sqrt(Sy2*(1/500-1/N))*100; hw500_ppi = z*math.sqrt(Sr2*(1/500-1/N))*100
    rows.append(dict(model=m, N=N, pi=round(pi,3), rho=round(rho,3), hw500_classical_pp=round(hw500_cls,2),
                     hw500_certified_pp=round(hw500_ppi,2),
                     **{f"n_pm{int(w*100)}pp": nstar(Sr2, N, w) for w in (0.05, 0.03, 0.02, 0.01)},
                     n_pm2pp_classical=nstar(Sy2, N, 0.02), n_pm2pp_infiniteN=math.ceil(z*z*Sr2/0.02**2)))
T = pd.DataFrame(rows); print(T.to_string(index=False))
print("\nhalf-width at n=500 (oracle, certified): %.2f-%.2f pp" % (T.hw500_certified_pp.min(), T.hw500_certified_pp.max()))
print("labels saved by predictions at +/-2pp: %d-%d" % ((T.n_pm2pp_classical-T.n_pm2pp).min(), (T.n_pm2pp_classical-T.n_pm2pp).max()))
print("max relative effect of finite N on n*(2pp): %.1f%%" % ((1 - T.n_pm2pp/T.n_pm2pp_infiniteN).max()*100))
T.to_csv("results/exp1_oracle_budgets.csv", index=False)
