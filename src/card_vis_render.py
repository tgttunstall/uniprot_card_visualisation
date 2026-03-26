#!/usr/bin/env python
from __future__ import annotations

import json
import os
from typing import Dict

import networkx as nx

try:
    from card_vis_extract import DEFAULT_COLORS
except ImportError:
    from .card_vis_extract import DEFAULT_COLORS

EDGE_COLORS = {
    "is_a": {"color": "olive", "font_color": "olivedrab"},
    "confers_resistance_to_antibiotic": {"color": "firebrick", "font_color": "indianred"},
    "confers_resistance_to_drug_class": {"color": "firebrick", "font_color": "indianred"},
}


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
        lbl = data.get("label")
        if lbl in EDGE_COLORS:
            data.update(EDGE_COLORS[lbl])


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
            font_color = graph.nodes[gid].get("font_color", theme_cfg["font"])
            if theme == "light" and str(font_color).lower() in {"white", "#ffffff", "#fff"}:
                font_color = theme_cfg["font"]
            node["font"] = {
                "size": graph.nodes[gid].get("font_size", 16),
                "color": font_color,
                "multi": True,
            }

    os.makedirs(os.path.dirname(os.path.abspath(html_file)), exist_ok=True)
    net.save_graph(str(html_file))


def trace_graph(graph: nx.MultiDiGraph, accession: str):
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

    return rows
