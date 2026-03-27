#!/usr/bin/env python
"""
Extract a bare CARD subgraph JSON (nodes/edges only) from local bulk files.

Defaults point to ~/amr paths and write to ~/card_output.
No env vars required; override via CLI flags.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from card_vis_extract import build_card_graph, to_payload  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Extract CARD subgraph to JSON")
    p.add_argument("--accession", default="Q182T3", help="UniProt accession")
    amr_root = os.path.join(os.path.expanduser("~"), "amr")
    p.add_argument("--map-file", default=os.path.join(amr_root, "map_tsv", "CARD-UniProt-Mapping.tsv"))
    p.add_argument("--obo-file", default=os.path.join(amr_root, "databases", "card", "ontology", "aro.obo"))
    p.add_argument("--card-json", default=os.path.join(amr_root, "databases", "card", "data", "card.json"))
    p.add_argument(
        "--categories-file",
        default=os.path.join(amr_root, "databases", "card", "data", "aro_categories.tsv"),
    )
    p.add_argument("--outdir", default=os.path.join(os.path.expanduser("~"), "card_output"))
    p.add_argument("--aro-root", help="Override ARO root (skip mapping)")
    p.add_argument("--include-uniprot", action="store_true", help="Include UniProt node and edge (default: off; pass flag to enable)")
    p.add_argument("--verbose", action="store_true", help="Print inputs")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    out_path = os.path.join(args.outdir, f"card_subgraph_{args.accession}.json")

    if not args.aro_root and not args.map_file:
        raise SystemExit("--map-file is required unless --aro-root is provided")

    if args.verbose:
        print(f"accession:   {args.accession}")
        print(f"aro_root:    {args.aro_root or 'lookup from map'}")
        print(f"map_file:    {args.map_file}")
        print(f"obo_file:    {args.obo_file}")
        print(f"card_json:   {args.card_json}")
        print(f"categories:  {args.categories_file}")
        print(f"out:         {out_path}")
        print(f"include UP:  {bool(args.include_uniprot)}")

    graph, aro = build_card_graph(
        accession=args.accession,
        map_file=args.map_file if args.map_file else "",
        obo_file=args.obo_file,
        card_json=args.card_json,
        categories_file=args.categories_file,
        aro_override=args.aro_root,
    )

    payload = to_payload(graph, aro_root=aro, accession=args.accession, include_uniprot=True)

    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Wrote subgraph JSON to {out_path}")


if __name__ == "__main__":
    main()
