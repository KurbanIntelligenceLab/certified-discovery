# Data dictionary

Per-figure and per-table source data. Every file also has an SHA-256 entry in
`run_metadata.json`. Columns below are read directly from the files.

## `budget_curves.csv`  (105 rows)

| column | example |
|---|---|
| `model` | EquiformerV3+DeNS-OAM |
| `n` | 50 |
| `w_classical` | 0.1530007347052582 |
| `w_certified` | 0.1613219055401501 |
| `coverage_classical` | 0.948 |
| `coverage_certified` | 0.96 |
| `n_rep` | 500 |
| `pool_N` | 43437 |
| `n_pred_pm2pct` | 1083 |

## `budgets_summary.csv`  (15 rows)

| column | example |
|---|---|
| `model` | EquiformerV3+DeNS-OAM |
| `pool_N` | 43437 |
| `n_empirical_pm2pct` | 800 |
| `n_pred_pm2pct` | 1083 |
| `w_certified_at_500` | 0.0511306897177674 |
| `rho_pool` | 0.2287242892410688 |
| `ratio_n400` | 0.9725488693779104 |

## `e5_robustness.csv`  (4 rows)

| column | example |
|---|---|
| `variant` | margins tau-0.01 |
| `model` | EquiformerV3+DeNS-OAM |
| `pool_N` | 32876 |
| `n_rep` | 200 |
| `mean_width` | 0.0448536890011316 |
| `coverage` | 0.92 |

## `e6_seed_robustness.csv`  (75 rows)

| column | example |
|---|---|
| `base_seed` | 0 |
| `model` | EquiformerV3+DeNS-OAM |
| `n_rep` | 500 |
| `coverage` | 0.928 |
| `mean_width` | 0.0494523389471861 |

## `fig2_budget_curve_synthetic.csv`  (6 rows)

| column | example |
|---|---|
| `truth` | 0.37535 |
| `imputation_estimate` | 0.5729 |
| `imputation_bias` | 0.1975499999999999 |
| `coverage_classical` | 0.948 |
| `coverage_ppi` | 0.944 |
| `mean_width_classical` | 0.2684654263194699 |
| `mean_width_ppi` | 0.2465944537385509 |
| `width_reduction` | 0.0814666263762873 |
| `n_label` | 50 |
| `n_rep` | 500 |
| `alpha` | 0.05 |

## `fig2_synthetic_summary.csv`  (44 rows)

| column | example |
|---|---|
| `section` | panel_a |
| `key` | true_precision |
| `value` | 0.37535 |

## `model_mae.csv`  (15 rows)

| column | example |
|---|---|
| `model` | EquiformerV3+DeNS-OAM |
| `mae_eV_per_atom` | 0.0174776231529298 |

## `table1_raw.csv`  (90 rows)

| column | example |
|---|---|
| `pool` | full |
| `tau` | 0.0 |
| `model` | EquiformerV3+DeNS-OAM |
| `flagged` | 43437 |
| `true` | 39364 |
| `ci_lo` | 38332 |
| `ci_hi` | 40479 |
| `overstate_pct` | 10.347017579514278 |
| `precision_gap` | 0.0937679858185418 |
| `coverage` | 0.931 |

## `table2_budget_sensitivity.csv`  (14 rows)

| column | example |
|---|---|
| `n_label` | 2000 |
| `pair` | EquiformerV3+DeNS-OAM vs eSEN-30M-OAM |
| `dq` | 0.0140712563627181 |
| `lo` | 0.0073400841703464 |
| `hi` | 0.0207750101541224 |
| `p` | 4.03150851950862e-05 |
| `err_order` | A<B |
| `p_holm` | 0.0002418905111705 |
| `agrees` | yes |

## `table2_raw.csv`  (14 rows)

| column | example |
|---|---|
| `pair` | EquiformerV3+DeNS-OAM vs eSEN-30M-OAM |
| `mae_A` | 0.0174776231529298 |
| `mae_B` | 0.0182143805441292 |
| `dq` | 0.013422460276406 |
| `lo` | -3.552049826199659e-05 |
| `hi` | 0.0267517047075945 |
| `p` | 0.049504407907146 |
| `err_order` | A<B |
| `p_holm` | 0.2970264474428763 |
| `agrees` | n.s. |

## `tableS2_raw.csv`  (6 rows)

| column | example |
|---|---|
| `scheme` | confidence tertiles |
| `model` | CGCNN |
| `n` | 500 |
| `pilot` | 100 |
| `n_rep` | 200 |
| `width_ratio` | 0.9944073041263288 |

## Revision experiment results (`../experiments/results/`)

| file | content |
|---|---|
| `exp0_census_reproduction.csv` | census counts recomputed from the public prediction files against Table 1 (five earlier models) |
| `exp1_oracle_budgets.csv` | half-widths at n = 500 and minimal budgets for target half-widths, Corollary 1 at census values (Supplementary Table 5) |
| `exp2_benchmark_transfer.csv`, `exp2_benchmark_transfer_arity.csv` | benchmark precision against restricted-pool precision by substitution round and by chemical arity (Supplementary Table 6) |
| `exp3_cost_proxy.csv` | realized cost of a 500-label sample relative to its expectation under size proxies (Supplementary Table 8) |
| `exp4_shared_budget.csv` | Holm-corrected detection rates and coverage for shared, split and per-pair designs (Supplementary Table 7) |
| `exp5_e1_reproduction.csv`, `exp5_e3_reproduction.csv` | re-execution of the coverage campaigns and paired comparisons against the run of record (five earlier models) |
| `exp5_e1_reproduction_15models.csv`, `exp5_e3_reproduction_15models.csv`, `exp4_shared_budget_15models.csv` | the same re-execution and the shared-sample comparison for all fifteen models (frontier files from figshare; run on Apple Silicon) |

Column meanings are documented in the docstring of the script that writes each file.
