#!/usr/bin/env python
"""
Render a CARD KG from a previously extracted subgraph JSON (PyVis only).
If --subgraph-json is not provided, the renderer builds the expected path from
--aro-id and --accession: ARO<number>_<ACCESSION>.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from card_vis_render import (
    apply_category_colors,
    apply_styling,
    load_payload,
    payload_to_graph,
    render_pyvis,
    trace_graph,
    DEFAULT_COLORS,
)


def parse_args():
    p = argparse.ArgumentParser(description="Render CARD KG from subgraph JSON")
    p.add_argument("--accession", required=True, help="UniProt accession")
    p.add_argument("--aro-id", required=True, help="CARD ARO accession, e.g. ARO:3007637")
    p.add_argument("--subgraph-json", default=None, help="Path to subgraph JSON; defaults to <outdir>/ARO<number>_<ACCESSION>.json")
    p.add_argument("--outdir", default=os.path.join(os.path.expanduser("~"), "card_output"))
    p.add_argument("--formats", default="pyvis", help="Comma list: pyvis")
    p.add_argument("--theme", choices=["dark", "light"], default="dark")
    p.add_argument("--trace", action="store_true", help="Write optional debug trace CSV")
    p.add_argument("--trace-json", action="store_true", help="Write optional debug styled nodes/edges JSON")
    return p.parse_args()


def payload_basename(aro_id: str, accession: str) -> str:
    return f"{aro_id.replace(':', '')}_{accession}"


def resolve_subgraph_path(args) -> str:
    if args.subgraph_json:
        return args.subgraph_json
    return os.path.join(args.outdir, f"{payload_basename(args.aro_id, args.accession)}.json")


def validate_payload(payload, args, subgraph_path: str) -> None:
    payload_accession = payload.get("uniprot")
    payload_aro = payload.get("aro_root")
    expected_base = payload_basename(args.aro_id, args.accession)
    actual_base = os.path.splitext(os.path.basename(subgraph_path))[0]

    if payload_accession != args.accession:
        raise SystemExit(f"Subgraph JSON accession mismatch: CLI accession {args.accession}, payload accession {payload_accession}")
    if payload_aro != args.aro_id:
        raise SystemExit(f"Subgraph JSON ARO mismatch: CLI ARO {args.aro_id}, payload ARO {payload_aro}")
    if actual_base != expected_base:
        raise SystemExit(f"Subgraph JSON filename mismatch: expected {expected_base}.json, got {os.path.basename(subgraph_path)}")


def main() -> None:
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    subgraph_path = resolve_subgraph_path(args)
    formats = {fmt.strip() for fmt in args.formats.split(',') if fmt.strip()}

    payload = load_payload(subgraph_path)
    validate_payload(payload, args, subgraph_path)
    graph = payload_to_graph(payload)
    # Ensure UniProt node is coloured/tagged, even if raw JSON stripped styling
    if args.accession in graph.nodes:
        graph.nodes[args.accession]["color"] = DEFAULT_COLORS.get("uniprot", "red")
        graph.nodes[args.accession]["group"] = "uniprot"
    apply_category_colors(graph, DEFAULT_COLORS)
    apply_styling(graph)

    output_base = os.path.splitext(os.path.basename(subgraph_path))[0]
    html_name = f"{output_base}.html"
    html_file = os.path.join(args.outdir, html_name)

    if "pyvis" in formats:
        render_pyvis(graph, html_file=html_file, theme=args.theme)
    if args.trace:
        rows = trace_graph(graph, accession=args.accession)
        trace_path = os.path.join(args.outdir, f"trace_{output_base}.csv")
        os.makedirs(os.path.dirname(os.path.abspath(trace_path)), exist_ok=True)
        if rows:
            fieldnames = [
                "UniProtKB",
                "ARO",
                "Name",
                "Category",
                "Source",
                "Color",
                "Edge Targets (ARO)",
                "Edge Labels",
                "Target Names",
            ]
            with open(trace_path, "w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(trace_path, "w") as fh:
                fh.write("")

    if args.trace_json:
        tj_path = os.path.join(args.outdir, f"trace_{output_base}.json")
        os.makedirs(os.path.dirname(os.path.abspath(tj_path)), exist_ok=True)
        payload = {
            "uniprot": args.accession,
            "nodes": [
                {"id": nid, **{k: v for k, v in data.items()}}
                for nid, data in graph.nodes(data=True)
            ],
            "edges": [
                {"source": src, "target": tgt, **{k: v for k, v in data.items()}}
                for src, tgt, data in graph.edges(data=True)
            ],
        }
        with open(tj_path, "w") as fh:
            json.dump(payload, fh, indent=2)

    print(f"Rendered to {html_file}")


if __name__ == "__main__":
    main()
