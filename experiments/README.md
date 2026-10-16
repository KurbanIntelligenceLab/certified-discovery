# Revision experiments (Digital Discovery, round 1)

Run from this directory. Inputs come either from `../data/` (after `bash fetch_data.sh`, which fetches the Matbench
Discovery v1.3.1 files and checks SHA-256) or, with `WBM_DATA_SOURCE=url`, streamed straight from their public URLs
into memory with nothing written to disk (GitHub files are checked against `../data/SHA256SUMS`, figshare files
against the sizes in `frontier_pred_files.json`):

    WBM_DATA_SOURCE=url python exp0_census_reproduction.py          # five models, streamed
    WBM_DATA_SOURCE=url MODELS=all python exp5_reproduce_e1_e3.py   # fifteen models, streamed (needs figshare access)

| Script | Purpose | Output |
|---|---|---|
| `exp0_census_reproduction.py` | Independent reproduction of Table 1 census counts, five earlier models | `results/exp0_*.csv` |
| `exp1_oracle_budgets.py` | Corollary 1 at census values (SI Table 5) | `results/exp1_*.csv` |
| `exp2_benchmark_transfer.py` | Benchmark-precision transfer (SI Table 6) | `results/exp2_*.csv` |
| `exp3_cost_proxy.py` | Verification cost under size proxies (SI Table 8) | `results/exp3_*.csv` |
| `exp4_shared_budget.py` | Shared versus per-pair verification samples (SI Table 7) | `results/exp4_*.csv` |
| `exp5_reproduce_e1_e3.py` | Exact re-execution of E1 and E3 for five models | `results/exp5_*.csv` |
| `verification/math_checks.py` | Exact/random checks of Theorem 1, Lemma 1, Corollary 1, Propositions 2-3 | stdout |
| `verification/ppi_py_crosscheck.py` | Point estimates versus `ppi_py` (requires `pip install ppi-python`) | stdout |

Then `python scripts/verify_results.py results experiments/results` from the repository root (exit code 0 when all 45 checks pass).

## Fifteen-model re-execution (frontier models)

The ten frontier models' prediction files are hosted on figshare (`frontier_pred_files.json` lists the exact
file for each model, 16.9 MB in total). On a machine with figshare access:

    bash fetch_frontier.sh                       # downloads to ../data/frontier/ and checks sizes
    MODELS=all python exp5_reproduce_e1_e3.py    # all 90 Table 1 / SI Table 1 configurations, all 14 pairs at n=500 and 2,000
    MODELS=all python exp4_shared_budget.py      # shared-sample design on the 15-model union

Outputs carry the suffix `_15models`. The `reproduce` GitHub Actions workflow runs exactly these commands on a hosted runner. Expected result if the pipeline matches the run of record: 90/90 and 28/28
identical rows. (The code path was exercised with stand-in files; the real files could not be fetched from the
verification environment because figshare is unreachable there.)
