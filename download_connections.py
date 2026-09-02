#!/usr/bin/env python
"""
download_connections.py -- fetch the Codex FAFB v783 *connections* export.

Why this exists: the project originally ran off `fafb_783_edge_list.csv`, a bare
pre->post pair list inherited from an earlier project. That file carries neither
synapse counts nor neuropil, which is why RESULTS.md previously listed both as
unavailable. They are available -- in this file:

    pre_root_id, post_root_id, neuropil, syn_count, nt_type

`connections.csv.gz` is Codex's standard export, thresholded at >=5 synapses per
(pre, post) pair summed across neuropils. The unthresholded variant is
`connections_no_threshold.csv.gz` at the same base URL if you ever need it.

Usage:  python3 download_connections.py [--force]
"""
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(ROOT, "data", "meta")

BASE = "https://storage.googleapis.com/flywire-data/codex/data"
DATASET, VERSION = "fafb", "783"
SOURCE_FILE = "connections.csv.gz"
LOCAL_FILE = "fafb_connections.csv.gz"


def main():
    force = "--force" in sys.argv
    os.makedirs(META, exist_ok=True)
    dst = os.path.join(META, LOCAL_FILE)

    if os.path.exists(dst) and not force:
        size_mb = os.path.getsize(dst) / 1e6
        print(f"have   {LOCAL_FILE}  ({size_mb:.0f} MB) -- use --force to re-download")
        return

    url = f"{BASE}/{DATASET}/{VERSION}/{SOURCE_FILE}"
    print(f"GET    {url}")
    try:
        urllib.request.urlretrieve(url, dst)
    except Exception as e:
        if os.path.exists(dst):
            os.remove(dst)
        print(f"FAIL   {e}\n")
        print("Fall back to the Codex 'Download data' page:")
        print("    https://codex.flywire.ai/api/download")
        print(f"    {DATASET} v{VERSION}: {SOURCE_FILE}  ->  data/meta/{LOCAL_FILE}")
        sys.exit(1)

    print(f"saved  data/meta/{LOCAL_FILE}  ({os.path.getsize(dst) / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
