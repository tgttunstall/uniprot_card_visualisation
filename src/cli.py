#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Set

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from card_vis_extract import DEFAULT_COLORS, attach_uniprot_node, build_card_graph  # noqa: E402
from card_vis_render import apply_styling, render_pyvis, trace_graph  # noqa: E402


def parse_accessions(args: argparse.Namespace) -> List[str]:
    accs: Set[str] = set()
    if args.accession:
        accs.update(args.accession)
    if args.accessions_file:
        with open(args.accessions_file) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    accs.add(line)
    if not accs:
        raise SystemExit("No accessions provided")
    return sorted(accs)


def ensure_outdir(path: str) -> str:
    path = os.path.expanduser(path)
    os.makedirs(path, exist_ok=True)
    return path


def handle_from_local(args: argparse.Namespace) -> None:
    outdir = ensure_outdir(args.outdir)
    accs = parse_accessions(args)

    for acc in accs:
        graph, aro = build_card_graph(
            accession=acc,
            map_file=args.map_file,
            obo_file=args.obo_file,
            card_json=args.card_json,
            categories_file=args.categories_file,
            colors=DEFAULT_COLORS,
        )
        graph = attach_uniprot_node(graph, acc, aro, DEFAULT_COLORS)
        apply_styling(graph)

        html_file = os.path.join(outdir, f"{acc}.html")
        render_pyvis(graph, html_file=html_file, theme=args.theme)

        if args.trace:
            df = trace_graph(graph, accession=acc)
            df.to_csv(os.path.join(outdir, f"trace_{acc}.csv"), index=False)
        if args.emit_raw:
            raw = {
                "nodes": [
                    {
                        "id": nid,
                        "name": data.get("name", nid),
                        "label": data.get("label", nid),
                        "def": data.get("def", ""),
                        "category": data.get("category"),
                        "sources": data.get("sources", []),
                        "title": data.get("title", data.get("def", "")),
                    }
                    for nid, data in graph.nodes(data=True)
                ],
                "edges": [
                    {
                        "source": src,
                        "target": tgt,
                        "label": edata.get("label", ""),
                        "title": edata.get("title", ""),
                    }
                    for src, tgt, edata in graph.edges(data=True)
                ],
            }
            with open(os.path.join(outdir, f"raw_{acc}.json"), "w") as fh:
                json.dump(raw, fh, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UniProt–CARD knowledge graph visualisation")
    common = parser
    common.add_argument("--accession", action="append", help="UniProt accession (repeatable)")
    common.add_argument("--accessions-file", help="File with UniProt accessions (one per line)")
    common.add_argument("--outdir", default=os.path.join(os.path.expanduser("~"), "card_output"), help="Output directory (default: ~/card_output)")
    common.add_argument("--theme", choices=["dark", "light"], default="dark", help="Visualisation theme")
    common.add_argument("--trace", action="store_true", help="Write trace CSV")
    common.add_argument("--emit-raw", action="store_true", help="Write raw nodes/edges JSON (no styling)")
    common.add_argument("--map-file", required=True)
    common.add_argument("--obo-file", required=True)
    common.add_argument("--card-json", required=True)
    common.add_argument("--categories-file", required=True)
    common.set_defaults(func=handle_from_local)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
