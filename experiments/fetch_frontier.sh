#!/usr/bin/env bash
# Fetch the ten frontier models' Matbench Discovery prediction files from figshare (needs figshare access).
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p ../data/frontier
python3 - <<'PY'
import json, os, urllib.request
man = json.load(open("frontier_pred_files.json"))
for m, v in man.items():
    dest = os.path.join("../data/frontier", os.path.basename(v["name"]))
    if os.path.isfile(dest) and (v.get("size") is None or os.path.getsize(dest) == v["size"]):
        print("present", m, dest); continue
    print("downloading", m, v["url"]); urllib.request.urlretrieve(v["url"], dest)
    if v.get("size") and os.path.getsize(dest) != v["size"]:
        raise SystemExit(f"size mismatch for {m}: got {os.path.getsize(dest)}, manifest says {v['size']}")
print("all frontier files present")
PY
