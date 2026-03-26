from __future__ import annotations

import json
import os
from typing import Dict

import networkx as nx


def graph_to_api_payload(
    accession: str,
    aro_root: str,
    graph: nx.MultiDiGraph,
    legend: Dict[str, str],
) -> Dict:
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


def payload_to_graph(payload: Dict) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    for node in payload.get("nodes", []):
        nid = node["id"]
        attrs = {k: v for k, v in node.items() if k != "id"}
        G.add_node(nid, **attrs)

    for edge in payload.get("edges", []):
        G.add_edge(edge["source"], edge["target"], **{k: v for k, v in edge.items() if k not in {"source", "target"}})

    return G


def save_payload(payload: Dict, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


def load_payload(path: str) -> Dict:
    with open(path, "r") as fh:
        return json.load(fh)
