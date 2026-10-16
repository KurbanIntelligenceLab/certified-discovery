# data/

Inputs for `experiments/` (not tracked, except `frontier/`).

- `experiments/fetch_data.sh` downloads the WBM summary and the five earlier models'
  prediction files from the Matbench Discovery repository at tag v1.3.1 into this
  directory and checks them against `SHA256SUMS`.
- `frontier/` holds the ten frontier models' discovery prediction files (see
  `experiments/frontier_pred_files.json` for names, figshare URLs and sizes;
  `experiments/fetch_frontier.sh` downloads them on a machine with figshare access).
  They are tracked in git so that `MODELS=all` runs work from a clone.

The `results/` directory of the repository (run of record) does not depend on anything
here; these inputs are only needed to re-execute the experiments.
