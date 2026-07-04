# figures/

Scripts that regenerate every visual in the project from the data in `../data/`.
Run them from the repository root.

- **`build_figures.py`** — regenerates the paper figures (Figure 2, the synthetic
  positive control, and Figure 3, the budget and calibration panels) as both
  vector PDF and 600 dpi PNG.

  ```bash
  python figures/build_figures.py            # 600 dpi (default)
  python figures/build_figures.py --dpi 300  # custom raster resolution
  ```

- **`make_assets.py`** — regenerates the README visuals (the hero banner, the
  method diagram, and the headline overstatement figure) into `../docs/assets/`.

  ```bash
  python figures/make_assets.py
  ```

Both read the released result files in `../data/`; nothing here downloads data or
recomputes results. To regenerate the underlying numbers, run
`notebooks/analysis.ipynb`.
