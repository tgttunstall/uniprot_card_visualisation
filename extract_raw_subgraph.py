#!/usr/bin/env python
"""
Extract a bare subgraph (nodes/edges only, no styling) for a UniProt accession.

Usage example:
  python extract_raw_subgraph.py \
    --accession Q182T3 \
    --map-file /home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv \
    --obo-file /home/tunstall/amr/databases/card/ontology/aro.obo \
    --card-json /home/tunstall/amr/databases/card/data/card.json \
    --categories-file /home/tunstall/amr/databases/card/data/aro_categories.tsv \
    --out raw_Q182T3.json

The output JSON contains only nodes (id, name, label, def, category, sources)
and edges (source, target, label, title). Colours and other visual properties
are intentionally omitted.
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

from cardviz.graph_builder import build_card_graph, attach_uniprot_node  # noqa: E402


def _bare_payload(graph):
    nodes = []
    for nid, data in graph.nodes(data=True):
        nodes.append(
            {
                "id": nid,
                "name": data.get("name", nid),
                "label": data.get("label", nid),
                "def": data.get("def", ""),
                "category": data.get("category"),
                "sources": data.get("sources", []),
            }
        )

    edges = []
    for src, tgt, edata in graph.edges(data=True):
        edges.append(
            {
                "source": src,
                "target": tgt,
                "label": edata.get("label", ""),
                "title": edata.get("title", ""),
            }
        )

    return {"nodes": nodes, "edges": edges}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract bare CARD subgraph for a UniProt accession")
    p.add_argument("--accession", required=True)
    p.add_argument("--map-file", required=True)
    p.add_argument("--obo-file", required=True)
    p.add_argument("--card-json", required=True)
    p.add_argument("--categories-file", required=True)
    p.add_argument("--out", required=True, help="Output JSON path for the bare subgraph")
    p.add_argument("--include-uniprot", action="store_true", help="Include UniProt node and edge to ARO root")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    graph, aro = build_card_graph(
        accession=args.accession,
        map_file=args.map_file,
        obo_file=args.obo_file,
        card_json=args.card_json,
        categories_file=args.categories_file,
        colors={},
    )

    if args.include_uniprot:
        graph = attach_uniprot_node(graph, args.accession, aro, {"uniprot": ""})

    payload = _bare_payload(graph)

    out_path = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Wrote bare subgraph to {out_path}")


if __name__ == "__main__":
    main()
