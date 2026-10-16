"""Independent loader for the WBM census and the model prediction files.
Convention (Matbench Discovery): predicted E_hull = DFT E_hull + (E_form,pred - E_form,DFT),
i.e. the model's formation energy placed against the MP2020-corrected DFT convex hull.
Predictions with |E_form,pred - E_form,DFT| > 5 eV/atom are treated as missing.

Data source (environment variable WBM_DATA_SOURCE):
  local  (default)  read from ../data/ (fetched by fetch_data.sh / fetch_frontier.sh)
  url               stream every file straight from its public URL into memory; nothing is
                    written to disk. GitHub-hosted files are checked against data/SHA256SUMS,
                    figshare-hosted frontier files against the sizes in frontier_pred_files.json.
"""
import hashlib, io, json, os, urllib.request
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
SOURCE = os.environ.get("WBM_DATA_SOURCE", "local")
TRUTH, EFORM = "e_above_hull_mp2020_corrected_ppd_mp", "e_form_per_atom_mp2020_corrected"
GH = "https://github.com/janosh/matbench-discovery/raw/v1.3.1/"
WBM_FILE = "2023-12-13-wbm-summary.csv.gz"
WBM_URL = GH + "data/wbm/" + WBM_FILE
FILES = {"CHGNet": "2023-12-21-chgnet-0.3.0-wbm-IS2RE.csv.gz", "M3GNet": "2023-12-28-m3gnet-wbm-IS2RE.csv.gz",
         "MEGNet": "2022-11-18-megnet-wbm-IS2RE.csv.gz", "ALIGNN": "2023-06-02-alignn-wbm-IS2RE.csv.gz",
         "CGCNN": "2023-01-26-cgcnn-ens=10-wbm-IS2RE.csv.gz"}
FILE_URLS = {"CHGNet": GH + "models/chgnet/" + FILES["CHGNet"], "M3GNet": GH + "models/m3gnet/" + FILES["M3GNet"],
             "MEGNet": GH + "models/megnet/" + FILES["MEGNet"], "ALIGNN": GH + "models/alignn/" + FILES["ALIGNN"],
             "CGCNN": GH + "models/cgcnn/" + FILES["CGCNN"]}
MARGIN_SCALE = 0.05
# The ten frontier models: discovery prediction files hosted on figshare (frontier_pred_files.json).
_MANIFEST = json.load(open(os.path.join(HERE, "frontier_pred_files.json"))) if os.path.isfile(os.path.join(HERE, "frontier_pred_files.json")) else {}
FRONTIER = {m: os.path.join("frontier", os.path.basename(v["name"])) for m, v in _MANIFEST.items()}
FRONTIER_URLS = {m: v["url"] for m, v in _MANIFEST.items()}
FRONTIER_SIZES = {m: v.get("size") for m, v in _MANIFEST.items()}
PAPER_ORDER = ["EquiformerV3+DeNS-OAM", "eSEN-30M-OAM", "PET-OAM-XL", "GRACE-2L-OAM", "ORB v3", "SevenNet-MF-ompa", "MACE-MPA-0",
               "MatRIS-10M-OAM", "DPA3-v1-OpenLAM", "MatterSim v1 5M", "CHGNet", "M3GNet", "ALIGNN", "MEGNet", "CGCNN"]

def _known_sha(fname):
    p = os.path.join(DATA, "SHA256SUMS")
    if not os.path.isfile(p): return None
    for line in open(p):
        h, _, n = line.strip().partition("  ")
        if n.strip() == fname: return h
    return None

def _stream(url, fname=None, expected_size=None):
    """Fetch a file into memory (no disk write) and check it against the recorded checksum or size."""
    with urllib.request.urlopen(url, timeout=120) as r:
        b = r.read()
    sha = _known_sha(fname) if fname else None
    if sha and hashlib.sha256(b).hexdigest() != sha:
        raise ValueError(f"checksum mismatch for {fname} streamed from {url}")
    if expected_size and len(b) != expected_size:
        raise ValueError(f"size mismatch for {url}: got {len(b)} bytes, manifest says {expected_size}")
    return io.BytesIO(b)

def _read_csv(local_rel, url, fname=None, expected_size=None):
    if SOURCE == "url":
        return pd.read_csv(_stream(url, fname, expected_size), compression="gzip")
    return pd.read_csv(os.path.join(DATA, local_rel))

def _pred_column(p, m):
    """Single formation-energy prediction column of a Matbench Discovery prediction file."""
    cols = [c for c in p.columns if c.startswith("e_form_per_atom")]
    if len(cols) != 1:
        cols = [c for c in p.columns if c.endswith("_pred_ens")]
    if len(cols) != 1:
        raise ValueError(f"{m}: cannot identify the prediction column; columns are {list(p.columns)}")
    return cols[0]

def load(models="five"):
    """models: 'five' (earlier graph networks), 'all' (plus the ten frontier models), or a list of model names.
    With WBM_DATA_SOURCE=url every file is streamed from its public URL and nothing is written to disk."""
    wbm = _read_csv(WBM_FILE, WBM_URL, WBM_FILE).set_index("material_id")
    files = dict(FILES)
    if models == "all" or (isinstance(models, (list, tuple)) and any(m in FRONTIER for m in models)):
        if SOURCE != "url":
            missing = [m for m in FRONTIER if not os.path.isfile(os.path.join(DATA, FRONTIER[m]))]
            if missing and models == "all":
                raise FileNotFoundError("frontier prediction files missing in data/frontier/: " + ", ".join(missing) +
                                        " (run experiments/fetch_frontier.sh, or set WBM_DATA_SOURCE=url to stream them)")
        files.update(FRONTIER)
    if isinstance(models, (list, tuple)):
        files = {m: files[m] for m in models}
    each_pred = {}
    for m, f in files.items():
        url = FRONTIER_URLS.get(m) or FILE_URLS.get(m)
        p = _read_csv(f, url, os.path.basename(f), FRONTIER_SIZES.get(m)).set_index("material_id")
        e = p[_pred_column(p, m)].reindex(wbm.index)
        e = e.where((e - wbm[EFORM]).abs() <= 5.0)
        each_pred[m] = wbm[TRUTH] + e - wbm[EFORM]
    return wbm, each_pred  # insertion order: the five earlier models, then the frontier models

def campaign(wbm, ep, tau, uniq=False):
    """Flagged pool S of one model: returns (index, y, f) with f the monotone margin in [0.5, 1]."""
    ok = ep.notna() & wbm[TRUTH].notna()
    if uniq:
        ok &= wbm["unique_prototype"].astype(bool)
    flag = ok & (ep <= tau)
    y = (wbm.loc[flag, TRUTH] <= tau).to_numpy(float)
    f = 1.0 / (1.0 + np.exp((ep[flag].to_numpy(float) - tau) / MARGIN_SCALE))
    return wbm.index[flag], y, f
