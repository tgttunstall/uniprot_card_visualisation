from __future__ import annotations

from pathlib import Path
from typing import Iterable

import networkx as nx
from pyvis.network import Network


def _pyvis_colors(theme: str) -> dict:
    if theme == "light":
        return {"bg": "#ffffff", "font": "#111111", "edge": "#666666"}
    return {"bg": "#222222", "font": "#ffffff", "edge": "#aaaaaa"}


def render_pyvis(graph: nx.MultiDiGraph, html_file: Path, theme: str = "dark") -> None:
    theme_cfg = _pyvis_colors(theme)
    net = Network(notebook=False, height="1200px", width="100%", bgcolor=theme_cfg["bg"], font_color=theme_cfg["font"])

    # Keep physics/arrow/options similar to original card_analysis styling
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

    # apply node colors/fonts after add_node
    for node in net.nodes:
        gid = node["id"]
        if gid in graph.nodes:
            node["color"] = graph.nodes[gid].get("color")
            node["font"] = {
                "size": graph.nodes[gid].get("font_size", 16),
                "color": graph.nodes[gid].get("font_color", theme_cfg["font"]),
                "multi": True,
            }

    html_file.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(html_file))


def render_png(graph: nx.MultiDiGraph, png_file: Path, layout: str = "spring") -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    png_file.parent.mkdir(parents=True, exist_ok=True)

    # Layout
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
