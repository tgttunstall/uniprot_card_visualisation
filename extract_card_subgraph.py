#!/usr/bin/env python
"""
Extract a bare CARD subgraph as JSON (nodes/edges, no styling).
Uses aro.obo for structure, aro_categories.tsv for categories, card.json for variants.
Optionally includes the UniProt node with an edge to the root ARO.
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

from card_vis_functions import card_graph, to_payload, DEFAULT_COLORS  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract bare CARD subgraph as JSON")
    p.add_argument("--accession", required=True)
    p.add_argument("--aro-root", help="Override ARO root (skip mapping)")
    p.add_argument("--map-file", help="Mapping TSV (required unless --aro-root provided)")
    p.add_argument("--obo-file", required=True)
    p.add_argument("--card-json", required=True)
    p.add_argument("--categories-file", required=True)
    p.add_argument("--out", required=True, help="Output JSON path")
    p.add_argument("--include-uniprot", action="store_true", help="Include UniProt node and edge to ARO root if provided")
    p.add_argument("--verbose", action="store_true", help="Print resolved ARO root and inputs")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.aro_root and not args.map_file:
        raise SystemExit("--map-file is required unless --aro-root is provided")

    if args.verbose:
        print(f"accession:   {args.accession}")
        print(f"aro_root:    {args.aro_root or 'lookup from map'}")
        if args.map_file:
            print(f"map_file:    {args.map_file}")
        print(f"obo_file:    {args.obo_file}")
        print(f"card_json:   {args.card_json}")
        print(f"categories:  {args.categories_file}")
        print(f"out:         {args.out}")
        print(f"include UP:  {bool(args.include_uniprot)}")

    graph, aro = card_graph(
        accession=args.accession,
        map_file=args.map_file if args.map_file else "",
        obo_file=args.obo_file,
        card_json=args.card_json,
        categories_file=args.categories_file,
        colors=DEFAULT_COLORS,
        aro_override=args.aro_root,
    )

    payload = to_payload(graph, aro_root=aro, accession=args.accession, include_uniprot=args.include_uniprot)

    out_path = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Wrote subgraph JSON to {out_path}")


if __name__ == "__main__":
    main()
