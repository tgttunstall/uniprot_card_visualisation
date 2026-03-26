#!/usr/bin/env python
from __future__ import annotations

import json
import os
from typing import Dict

import networkx as nx
import pandas as pd

try:
    from card_vis_extract import DEFAULT_COLORS
except ImportError:
    # allow relative import when running as module
    from .card_vis_extract import DEFAULT_COLORS


def apply_category_colors(graph: nx.MultiDiGraph, colors: Dict[str, str] = DEFAULT_COLORS) -> None:
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


def _wrap(text: str, n: int) -> str:
    words = text.split()
    lines = []
    current: list[str] = []
    for w in words:
        current.append(w)
        if len(" ".join(current)) >= n:
            lines.append(" ".join(current))
            current = []
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def apply_styling(graph: nx.MultiDiGraph) -> None:
    for node in graph.nodes:
        in_deg = graph.in_degree(node)
        graph.nodes[node]["label"] = _wrap(str(graph.nodes[node].get("label", "")), 35)
        graph.nodes[node]["title"] = _wrap(str(graph.nodes[node].get("title", "")), 80)
        graph.nodes[node]["font_size"] = 45 + in_deg * 2
        graph.nodes[node]["size"] = 25 + in_deg * 6
        graph.nodes[node]["font_color"] = graph.nodes[node].get("font_color", "white")

    for _, _, _, data in graph.edges(keys=True, data=True):
        data["width"] = 2
        data["font_size"] = 18
        data["font_face"] = "arial"
        data["font_color"] = "gray"
        if data.get("label") == "is_a":
            data["color"] = "olive"
            data["font_color"] = "olivedrab"
        elif data.get("label") and "confers_resistance_to" in data["label"]:
            data["color"] = "firebrick"
            data["font_color"] = "indianred"


def payload_to_graph(payload: Dict) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    for node in payload.get("nodes", []):
        nid = node["id"]
        attrs = {k: v for k, v in node.items() if k != "id"}
        G.add_node(nid, **attrs)

    for edge in payload.get("edges", []):
        G.add_edge(edge["source"], edge["target"], **{k: v for k, v in edge.items() if k not in {"source", "target"}})

    return G


def load_payload(path: str) -> Dict:
    with open(path, "r") as fh:
        return json.load(fh)


def save_payload(payload: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


def graph_to_api_payload(accession: str, aro_root: str, graph: nx.MultiDiGraph, legend: Dict[str, str]) -> Dict:
    nodes = []
    for node, data in graph.nodes(data=True):
        nodes.append(
            {
                "id": node,
                "name": data.get("name", node),
                "label": data.get("label", node),
                "def": data.get("def", ""),
                "category": data.get("category"),
                "group": data.get("group"),
                "color": data.get("color"),
                "sources": data.get("sources", []),
                "title": data.get("title", ""),
            }
        )

    edges = []
    for src, tgt, data in graph.edges(data=True):
        edges.append(
            {
                "source": src,
                "target": tgt,
                "label": data.get("label", ""),
                "title": data.get("title", ""),
            }
        )

    return {
        "uniprot": {"id": accession, "label": accession},
        "aro_root": aro_root,
        "nodes": nodes,
        "edges": edges,
        "legend": legend,
    }


def render_pyvis(graph: nx.MultiDiGraph, html_file: str, theme: str = "dark") -> None:
    from pyvis.network import Network

    theme_cfg = {"light": {"bg": "#ffffff", "font": "#111111", "edge": "#666666"}, "dark": {"bg": "#222222", "font": "#ffffff", "edge": "#aaaaaa"}}[theme]
    net = Network(notebook=False, height="1200px", width="100%", bgcolor=theme_cfg["bg"], font_color=theme_cfg["font"])

    net.set_options(
        """
        var options = {
          "nodes": {
            "color": {
              "highlight": {"border": "white", "background": "black"},
              "hover": {"border": "white", "background": "black"}
            }
          },
          "edges": {
            "color": {"color": "gray"},
            "font": {
              "color": "gray",
              "size": 16,
              "face": "arial",
              "background": "none",
              "strokeWidth": 0,
              "strokeColor": "none",
              "multi": true
            },
            "smooth": true,
            "arrows": {"to": {"enabled": true, "scaleFactor": 2}}
          },
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -20000,
              "centralGravity": 0.3,
              "springLength": 200,
              "springConstant": 0.01,
              "damping": 0.09
            },
            "minVelocity": 0.75
          }
        }
        """
    )

    for node, data in graph.nodes(data=True):
        net.add_node(
            node,
            label=data.get("label", node),
            title=data.get("title", ""),
            group=data.get("group", ""),
            size=data.get("size"),
        )

    for src, tgt, data in graph.edges(data=True):
        net.add_edge(
            src,
            tgt,
            width=data.get("width", 1),
            label=data.get("label", ""),
            title=data.get("title", ""),
            color=data.get("color", theme_cfg["edge"]),
            font={"size": data.get("font_size", 12), "color": data.get("font_color", theme_cfg["edge"]), "multi": True},
        )

    for node in net.nodes:
        gid = node["id"]
        if gid in graph.nodes:
            node["color"] = graph.nodes[gid].get("color")
            node["font"] = {
                "size": graph.nodes[gid].get("font_size", 16),
                "color": graph.nodes[gid].get("font_color", theme_cfg["font"]),
                "multi": True,
            }

    os.makedirs(os.path.dirname(os.path.abspath(html_file)), exist_ok=True)
    net.save_graph(str(html_file))


def render_png(graph: nx.MultiDiGraph, png_file: str, layout: str = "spring") -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    os.makedirs(os.path.dirname(os.path.abspath(png_file)), exist_ok=True)

    if layout == "spring":
        k_value = 1 / max(1, np.sqrt(len(graph.nodes())))
        pos = nx.spring_layout(graph, k=k_value, iterations=500, seed=42)
    elif layout == "circular":
        pos = nx.circular_layout(graph)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(graph)
    else:
        pos = nx.spring_layout(graph, k=1 / max(1, np.sqrt(len(graph.nodes()))), iterations=500, seed=42)

    node_colors = [graph.nodes[n].get("color", "#1f78b4") for n in graph.nodes()]
    node_sizes = [graph.nodes[n].get("size", 20) * 4 for n in graph.nodes()]
    node_labels = {n: graph.nodes[n].get("label", n) for n in graph.nodes()}
    node_font_sizes = {n: graph.nodes[n].get("font_size", 16) for n in graph.nodes()}

    edge_colors = [graph.edges[e].get("color", "#999999") for e in graph.edges(keys=True)]
    edge_widths = [graph.edges[e].get("width", 1.5) for e in graph.edges(keys=True)]
    edge_labels = {(u, v): d.get("label", "") for u, v, d in graph.edges(data=True)}

    plt.figure(figsize=(16, 16), dpi=150)
    nx.draw(
        graph,
        pos,
        with_labels=False,
        node_size=node_sizes,
        node_color=node_colors,
        edge_color=edge_colors,
        width=edge_widths,
        alpha=0.9,
    )

    for node, (x, y) in pos.items():
        plt.text(x, y, s=node_labels[node], fontsize=node_font_sizes[node], ha="center", va="center", color="white")

    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_color="gray", font_size=10, bbox=dict(alpha=0))

    plt.axis("off")
    plt.savefig(png_file, format="PNG", facecolor="white")
    plt.close()


def trace_graph(graph: nx.MultiDiGraph, accession: str) -> pd.DataFrame:
    rows = []
    for node, data in graph.nodes(data=True):
        edges = list(graph.edges(node, keys=True, data=True))
        targets = [t for (_, t, _, _) in edges]
        labels = [str(d.get("label", k)) for (_, _, k, d) in edges]
        target_names = [graph.nodes[t].get("name", t) for t in targets]

        rows.append(
            {
                "UniProtKB": accession,
                "ARO": node,
                "Name": data.get("name", node),
                "Category": data.get("category", ""),
                "Source": ";".join(sorted(set(data.get("sources", [])))),
                "Color": data.get("color", ""),
                "Edge Targets (ARO)": ";".join(targets) if targets else "",
                "Edge Labels": ";".join(labels) if labels else "",
                "Target Names": ";".join(target_names) if target_names else "",
            }
        )

    return pd.DataFrame(rows)
