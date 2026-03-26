from __future__ import annotations

import argparse
import json
import os
from typing import List, Set

from cardviz.graph_builder import build_card_graph, attach_uniprot_node, apply_styling
from cardviz.api_payload import graph_to_api_payload, payload_to_graph, save_payload, load_payload
from cardviz.visualize import render_pyvis, render_png
from cardviz.trace_utils import trace_graph


DEFAULT_COLORS = {
    "card": "blue",
    "Antibiotic": "rebeccapurple",
    "Drug Class": "mediumorchid",
    "AMR Gene Family": "steelblue",
    "Resistance Mechanism": "deepskyblue",
    "uniprot": "red",
}


def apply_category_colors(graph, colors):
    for nid, data in graph.nodes(data=True):
        if data.get("color"):
            continue
        cat = data.get("category") or data.get("group")
        if cat in colors:
            graph.nodes[nid]["color"] = colors[cat]
            graph.nodes[nid]["group"] = cat
        else:
            graph.nodes[nid]["color"] = colors.get("card", "blue")
            graph.nodes[nid]["group"] = data.get("group", "card")
        graph.nodes[nid].setdefault("font_color", "white")
        if not graph.nodes[nid].get("title"):
            graph.nodes[nid]["title"] = f"{nid}: {graph.nodes[nid].get('name', nid)}; {graph.nodes[nid].get('def', '')}"


def _raw_payload(graph) -> dict:
    nodes = []
    for nid, data in graph.nodes(data=True):
        title = data.get("title")
        if not title:
            title = f"{nid}: {data.get('name', nid)}; {data.get('def', '')}"
        nodes.append(
            {
                "id": nid,
                "name": data.get("name", nid),
                "label": data.get("label", nid),
                "def": data.get("def", ""),
                "category": data.get("category"),
                "sources": data.get("sources", []),
                "title": title,
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
    formats = {fmt.strip() for fmt in args.formats.split(',') if fmt.strip()}

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
        png_file = os.path.join(outdir, f"{acc}.png")

        if "pyvis" in formats:
            render_pyvis(graph, html_file=html_file, theme=args.theme)
        if "png" in formats:
            render_png(graph, png_file=png_file)

        if args.trace:
            df = trace_graph(graph, accession=acc)
            df.to_csv(os.path.join(outdir, f"trace_{acc}.csv"), index=False)
        if args.emit_raw:
            raw = _raw_payload(graph)
            with open(os.path.join(outdir, f"raw_{acc}.json"), "w") as fh:
                json.dump(raw, fh, indent=2)


def handle_from_api(args: argparse.Namespace) -> None:
    outdir = ensure_outdir(args.outdir)
    formats = {fmt.strip() for fmt in args.formats.split(',') if fmt.strip()}
    mode = args.api_mode

    if mode == "create":
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

            payload = graph_to_api_payload(acc, aro, graph, legend=DEFAULT_COLORS)
            api_name = args.api_json_name or f"card_api_mock_{acc}.json"
            save_payload(payload, os.path.join(outdir, api_name))

            html_file = os.path.join(outdir, f"{acc}.html")
            png_file = os.path.join(outdir, f"{acc}.png")
            if "pyvis" in formats:
                render_pyvis(graph, html_file=html_file, theme=args.theme)
            if "png" in formats:
                render_png(graph, png_file=png_file)
            if args.trace:
                df = trace_graph(graph, accession=acc)
                df.to_csv(os.path.join(outdir, f"trace_{acc}.csv"), index=False)

    elif mode == "use":
        if not args.api_json_path:
            raise SystemExit("--api-json-path is required in 'use' mode")
        payload = load_payload(args.api_json_path)
        # If payload is a string (path), load it; otherwise expect dict
        if isinstance(payload, str):
            with open(payload, "r") as fh:
                payload = json.load(fh)
        graph = payload_to_graph(payload)
        apply_category_colors(graph, DEFAULT_COLORS)
        apply_styling(graph)

        acc = payload.get("uniprot")
        if isinstance(acc, dict):
            acc = acc.get("id", acc.get("accession", acc))
        if not acc:
            acc = args.accession[0] if args.accession else "graph"
        html_file = os.path.join(outdir, f"{acc}.html")
        png_file = os.path.join(outdir, f"{acc}.png")
        if "pyvis" in formats:
            render_pyvis(graph, html_file=html_file, theme=args.theme)
        if "png" in formats:
            render_png(graph, png_file=png_file)
        if args.trace:
            df = trace_graph(graph, accession=acc)
            df.to_csv(os.path.join(outdir, f"trace_{acc}.csv"), index=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UniProt–CARD knowledge graph visualisation")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--accession", action="append", help="UniProt accession (repeatable)")
    common.add_argument("--accessions-file", help="File with UniProt accessions (one per line)")
    common.add_argument("--outdir", default=os.path.join(os.path.expanduser("~"), "card_output"), help="Output directory (default: ~/card_output)")
    common.add_argument("--formats", default="pyvis,png", help="Comma list: pyvis,png (default: pyvis,png)")
    common.add_argument("--theme", choices=["dark", "light"], default="dark", help="Visualisation theme")
    common.add_argument("--trace", action="store_true", help="Write trace CSV")
    common.add_argument("--emit-raw", action="store_true", help="Write raw nodes/edges JSON (no styling)")

    local = subparsers.add_parser("from-local", parents=[common], help="Build from CARD flat files")
    local.add_argument("--map-file", required=True)
    local.add_argument("--obo-file", required=True)
    local.add_argument("--card-json", required=True)
    local.add_argument("--categories-file", required=True)
    local.set_defaults(func=handle_from_local)

    api = subparsers.add_parser("from-api-json", parents=[common], help="Generate or consume API-style JSON")
    api.add_argument("--api-mode", choices=["create", "use"], required=True, help="create: build mock JSON; use: load existing JSON")
    api.add_argument("--api-json-name", help="Filename for mock JSON (default card_api_mock_<ACC>.json)")
    api.add_argument("--api-json-path", help="Path to existing API JSON when using 'use' mode")
    api.add_argument("--map-file")
    api.add_argument("--obo-file")
    api.add_argument("--card-json")
    api.add_argument("--categories-file")
    api.set_defaults(func=handle_from_api)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
