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
    url = v.get("download_url") or "https://api.figshare.com/v2/file/download/" + v["url"].rstrip("/").split("/")[-1]
    print("downloading", m, url)
    req = urllib.request.Request(url, headers={"User-Agent": "certified-discovery/1.1 (python-urllib)"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    if v.get("size") and os.path.getsize(dest) != v["size"]:
        got = os.path.getsize(dest); os.remove(dest)
        raise SystemExit(f"size mismatch for {m}: got {got} bytes from {url}, manifest says {v['size']}; "
                         "the file was not kept")
print("all frontier files present")
PY
