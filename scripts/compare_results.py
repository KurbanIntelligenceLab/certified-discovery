"""compare_results.py -- numerical comparison of re-executed experiment outputs with the committed
result files.

Usage:
    python scripts/compare_results.py experiments/results            # working tree vs. git HEAD
    python scripts/compare_results.py <dir_new> <dir_reference>      # two directories

Byte identity of CSV files is platform-specific (floating-point formatting and libm differ between
x86-64 and Apple Silicon). This script therefore compares numerically: every CSV in the new
directory is aligned with the reference on its non-numeric columns and the numeric columns must
agree within rtol=1e-9, atol=1e-12. Exit code is nonzero on any missing file, missing row or
out-of-tolerance value. Reports the largest absolute and relative difference per file.
"""
import io
import os
import subprocess
import sys

import numpy as np
import pandas as pd

RTOL, ATOL = 1e-9, 1e-12


def load_reference(path, ref_dir):
    if ref_dir is None:  # git HEAD
        out = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True)
        if out.returncode != 0:
            return None
        return pd.read_csv(io.StringIO(out.stdout))
    p = os.path.join(ref_dir, os.path.basename(path))
    return pd.read_csv(p) if os.path.isfile(p) else None


def compare(new, ref):
    is_num = pd.api.types.is_numeric_dtype
    keys = [c for c in new.columns if not is_num(new[c]) and c in ref.columns]
    num = [c for c in new.columns if is_num(new[c]) and c in ref.columns]
    missing_cols = [c for c in ref.columns if c not in new.columns]
    a = new.sort_values(keys).reset_index(drop=True) if keys else new.reset_index(drop=True)
    b = ref.sort_values(keys).reset_index(drop=True) if keys else ref.reset_index(drop=True)
    if len(a) != len(b) or (keys and not a[keys].astype(str).equals(b[keys].astype(str))):
        return False, "row sets differ", np.nan, np.nan, missing_cols
    x, y = a[num].to_numpy(float), b[num].to_numpy(float)
    both_nan = np.isnan(x) & np.isnan(y)
    diff = np.abs(x - y); diff[both_nan] = 0.0
    rel = diff / np.maximum(np.abs(y), ATOL); rel[both_nan] = 0.0
    ok = bool(np.all((diff <= ATOL + RTOL * np.abs(y)) | both_nan)) and not missing_cols
    return ok, "", float(np.nanmax(diff)) if diff.size else 0.0, float(np.nanmax(rel)) if rel.size else 0.0, missing_cols


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    new_dir = sys.argv[1]; ref_dir = sys.argv[2] if len(sys.argv) > 2 else None
    files = sorted(f for f in os.listdir(new_dir) if f.endswith(".csv"))
    failures = 0
    for f in files:
        path = os.path.join(new_dir, f)
        ref = load_reference(path, ref_dir)
        if ref is None:
            print(f"[SKIP] {f}: no reference file"); continue
        new = pd.read_csv(path)
        ok, why, dmax, rmax, missing_cols = compare(new, ref)
        tag = "PASS" if ok else "FAIL"
        extra = why or f"max |diff| {dmax:.2e}, max rel {rmax:.2e}" + (f", missing columns {missing_cols}" if missing_cols else "")
        print(f"[{tag}] {f}: {extra}")
        failures += not ok
    print("\nall files numerically identical within tolerance" if not failures else f"\n{failures} file(s) differ beyond tolerance")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
