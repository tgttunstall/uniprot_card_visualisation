#!/usr/bin/env python
"""
Unified runner to extract a CARD subgraph JSON and/or render it.

Steps:
  extract: uses extract_card_subgraph.py to produce card_subgraph_<ACC>.json
  render:  renders from a given subgraph JSON via cardviz.cli (PyVis/PNG)

Defaults point to local CARD files under /home/tunstall/amr with no env vars.
All paths are absolute; output defaults to ~/card_output via os.path.expanduser.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def parse_args():
    p = argparse.ArgumentParser(description="Extract and/or render CARD KG")
    p.add_argument("--step", choices=["extract", "render", "both"], default="both")
    p.add_argument("--accession", default="Q182T3")
    p.add_argument("--map-file", default="/home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv")
    p.add_argument("--obo-file", default="/home/tunstall/amr/databases/card/ontology/aro.obo")
    p.add_argument("--card-json", default="/home/tunstall/amr/databases/card/data/card.json")
    p.add_argument("--categories-file", default="/home/tunstall/amr/databases/card/data/aro_categories.tsv")
    p.add_argument("--outdir", default=os.path.join(os.path.expanduser("~"), "card_output"))
    p.add_argument("--subgraph-json", default=None, help="Path to subgraph JSON (defaults to outdir/card_subgraph_<ACC>.json)")
    p.add_argument("--include-uniprot", action="store_true", help="Include UniProt node/edge in subgraph")
    p.add_argument("--formats", default="pyvis,png", help="Render formats: pyvis,png (comma list)")
    p.add_argument("--theme", choices=["dark", "light"], default="dark")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    subgraph_path = args.subgraph_json or os.environ.get("CARD_SUBGRAPH")
    if not subgraph_path:
        subgraph_path = os.path.join(args.outdir, f"card_subgraph_{args.accession}.json")

    if args.step in {"extract", "both"}:
        extract_cmd = [
            "python",
            os.path.join(ROOT, "extract_card_subgraph.py"),
            "--accession", args.accession,
            "--map-file", args.map_file,
            "--obo-file", args.obo_file,
            "--card-json", args.card_json,
            "--categories-file", args.categories_file,
            "--out", subgraph_path,
        ]
        if args.include_uniprot:
            extract_cmd.append("--include-uniprot")

        print("Running (extract):")
        print(" ".join(extract_cmd))
        subprocess.run(extract_cmd, check=True)
        print(f"Subgraph written to {subgraph_path}")

    if args.step in {"render", "both"}:
        render_cmd = [
            "python",
            os.path.join(ROOT, "run_render_kg.py"),
            "--accession",
            args.accession,
            "--subgraph-json",
            subgraph_path,
            "--outdir",
            args.outdir,
            "--formats",
            args.formats,
            "--theme",
            args.theme,
        ]

        print("Running (render):")
        print(" ".join(render_cmd))
        subprocess.run(render_cmd, check=True)


if __name__ == "__main__":
    main()
