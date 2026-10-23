#!/usr/bin/env bash
# Fetch the public inputs of the revision experiments (Matbench Discovery tag v1.3.1) and verify checksums.
set -euo pipefail
cd "$(dirname "$0")/../data"
B=https://github.com/janosh/matbench-discovery/raw/v1.3.1
for p in data/wbm/2023-12-13-wbm-summary.csv.gz models/chgnet/2023-12-21-chgnet-0.3.0-wbm-IS2RE.csv.gz \
         models/m3gnet/2023-12-28-m3gnet-wbm-IS2RE.csv.gz models/megnet/2022-11-18-megnet-wbm-IS2RE.csv.gz \
         models/alignn/2023-06-02-alignn-wbm-IS2RE.csv.gz "models/cgcnn/2023-01-26-cgcnn-ens=10-wbm-IS2RE.csv.gz"; do
  f=$(basename "$p"); [ -f "$f" ] || curl -sSL -o "$f" "$B/$p"
done
sha256sum -c SHA256SUMS
