#!/usr/bin/env python
"""
Describe input files and extract a bare CARD subgraph for a UniProt accession.

Outputs the same minimal JSON as extract_card_subgraph.py (nodes/edges, no
styling). Prints a short summary of which files are used and which ARO root is
resolved. You may also override the ARO root explicitly.

Examples:

python describe_and_extract.py \
  --accession Q182T3 \
  --map-file /home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv \
  --obo-file /home/tunstall/amr/databases/card/ontology/aro.obo \
  --card-json /home/tunstall/amr/databases/card/data/card.json \
  --categories-file /home/tunstall/amr/databases/card/data/aro_categories.tsv \
  --out /home/tunstall/card_output/card_subgraph_Q182T3.json \
  --include-uniprot

python describe_and_extract.py \
  --accession A6T5M6 \
  --aro-root ARO:3003373 \
  --obo-file /home/tunstall/amr/databases/card/ontology/aro.obo \
  --card-json /home/tunstall/amr/databases/card/data/card.json \
  --categories-file /home/tunstall/amr/databases/card/data/aro_categories.tsv \
  --out /home/tunstall/card_output/card_subgraph_A6T5M6.json \
  --include-uniprot
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from extract_card_subgraph import card_graph, to_payload, load_mapping  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Describe inputs and extract CARD subgraph JSON")
    p.add_argument("--accession", required=True, help="UniProt accession (used for naming; mapping if no aro-root override)")
    p.add_argument("--aro-root", help="Optional ARO root (skip mapping if provided)")
    p.add_argument("--map-file", help="Mapping TSV (required unless --aro-root provided)")
    p.add_argument("--obo-file", required=True, help="Path to aro.obo")
    p.add_argument("--card-json", required=True, help="Path to card.json (for variants)")
    p.add_argument("--categories-file", required=True, help="Path to aro_categories.tsv")
    p.add_argument("--out", required=True, help="Output JSON path")
    p.add_argument("--include-uniprot", action="store_true", help="Include UniProt node and edge to ARO root")
    return p.parse_args()


def main():
    args = parse_args()

    if args.aro_root:
        aro_root = args.aro_root
    else:
        if not args.map_file:
            raise SystemExit("--map-file is required unless --aro-root is provided")
        _, aro_root = load_mapping(args.map_file, args.accession)

    print("Inputs:")
    print(f"  UniProt accession: {args.accession}")
    print(f"  ARO root:          {aro_root}")
    if args.map_file:
        print(f"  Mapping TSV:      {args.map_file}")
    print(f"  aro.obo:          {args.obo_file}")
    print(f"  card.json:        {args.card_json}")
    print(f"  aro_categories:   {args.categories_file}")
    print(f"  Output JSON:      {args.out}")
    print(f"  Include UniProt:  {bool(args.include_uniprot)}")

    graph, _ = card_graph(
        accession=args.accession,
        map_file=args.map_file if args.map_file else "",
        obo_file=args.obo_file,
        card_json=args.card_json,
        categories_file=args.categories_file,
        aro_override=aro_root,
    )

    payload = to_payload(graph, aro_root=aro_root, accession=args.accession, include_uniprot=args.include_uniprot)

    out_path = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Wrote subgraph JSON to {out_path}")


if __name__ == "__main__":
    main()
