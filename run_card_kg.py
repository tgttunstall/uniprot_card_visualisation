#!/usr/bin/env python
"""
Convenience runner to:
1) Extract the bare CARD subgraph JSON for a UniProt accession (no styling).
2) Render the KG from that JSON (PyVis + PNG).

Defaults target local CARD files under /home/tunstall/amr; override via env vars:
  CARD_ACCESSION   (default: Q182T3)
  CARD_OUTDIR      (default: ~/card_output)
"""

from __future__ import annotations

import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Default inputs (edit if your paths differ)
MAP_FILE = "/home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv"
OBO_FILE = "/home/tunstall/amr/databases/card/ontology/aro.obo"
CARD_JSON = "/home/tunstall/amr/databases/card/data/card.json"
CATEGORIES = "/home/tunstall/amr/databases/card/data/aro_categories.tsv"

ACCESSION = os.environ.get("CARD_ACCESSION", "Q182T3")
OUTDIR = os.path.expanduser(os.environ.get("CARD_OUTDIR", os.path.join(os.path.expanduser("~"), "card_output")))


def main() -> None:
    raw_path = os.path.join(OUTDIR, f"card_subgraph_{ACCESSION}.json")

    # 1) Extract bare subgraph
    extract_cmd = [
        "python",
        os.path.join(ROOT, "extract_card_subgraph.py"),
        "--accession",
        ACCESSION,
        "--map-file",
        MAP_FILE,
        "--obo-file",
        OBO_FILE,
        "--card-json",
        CARD_JSON,
        "--categories-file",
        CATEGORIES,
        "--out",
        raw_path,
        "--include-uniprot",
    ]

    print("Running (extract):")
    print(" ".join(extract_cmd))
    subprocess.run(extract_cmd, check=True)

    # 2) Render from raw JSON
    render_cmd = [
        "python",
        "-m",
        "cardviz.cli",
        "from-api-json",
        "--api-mode",
        "use",
        "--api-json-path",
        raw_path,
        "--outdir",
        OUTDIR,
        "--formats",
        "pyvis,png",
        "--theme",
        "dark",
        "--accession",
        ACCESSION,
    ]

    print("Running (render):")
    print(" ".join(render_cmd))
    subprocess.run(render_cmd, check=True)


if __name__ == "__main__":
    main()
