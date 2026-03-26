#!/usr/bin/env python
"""
Render a CARD KG from a previously extracted subgraph JSON (PyVis only).
Defaults: subgraph in ~/card_output/card_subgraph_<ACC>.json, outputs to the
same outdir. No env vars required.
"""

from __future__ import annotations

import argparse
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
    p.add_argument("--accession", default="Q182T3")
    p.add_argument("--subgraph-json", default=None, help="Path to subgraph JSON (default: ~/card_output/card_subgraph_<ACC>.json)")
    p.add_argument("--outdir", default=os.path.join(os.path.expanduser("~"), "card_output"))
    p.add_argument("--formats", default="pyvis", help="Comma list: pyvis")
    p.add_argument("--theme", choices=["dark", "light"], default="dark")
    p.add_argument("--trace", action="store_true", help="Write trace CSV")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    subgraph_path = args.subgraph_json or os.path.join(args.outdir, f"card_subgraph_{args.accession}.json")
    formats = {fmt.strip() for fmt in args.formats.split(',') if fmt.strip()}

    payload = load_payload(subgraph_path)
    graph = payload_to_graph(payload)
    apply_category_colors(graph, DEFAULT_COLORS)
    apply_styling(graph)

    html_file = os.path.join(args.outdir, f"{args.accession}.html")

    if "pyvis" in formats:
        render_pyvis(graph, html_file=html_file, theme=args.theme)
    if args.trace:
        df = trace_graph(graph, accession=args.accession)
        df.to_csv(os.path.join(args.outdir, f"trace_{args.accession}.csv"), index=False)

    print(f"Rendered to {html_file}")


if __name__ == "__main__":
    main()
