# figures/

Scripts that regenerate every visual in the project from the data in `../results/`.
Run them from the repository root.

- **`build_figures.py`** regenerates the manuscript figures (Figure 2, the synthetic
  positive control, and Figure 3, the budget and calibration panels) as vector PDF and
  600 dpi PNG. The outputs used in the manuscript are tracked in `output/`; the script
  reproduces them from `../results/`, pixel-identical with matplotlib 3.10 (the version used for the manuscript figures, recorded in `figures/output/ENVIRONMENT.txt`); other versions reproduce the same figures with sub-pixel differences in text layout.

  ```bash
  python figures/build_figures.py results            # 600 dpi (default)
  python figures/build_figures.py results --dpi 300  # custom raster resolution
  ```

- **`make_assets.py`** regenerates the README visuals (hero banner, method diagram,
  headline overstatement figure) into `../docs/assets/`.

Both read the released result files in `../results/`; nothing here downloads data or
recomputes results. To regenerate the numbers, run `notebooks/analysis.ipynb`; to
re-execute the revision experiments, see `experiments/README.md`.
