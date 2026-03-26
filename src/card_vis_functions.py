#!/usr/bin/env python
from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List, Optional, Tuple

import networkx as nx
import obonet
import pandas as pd


DEFAULT_COLORS = {
    "card": "blue",
    "Antibiotic": "rebeccapurple",
    "Drug Class": "mediumorchid",
    "AMR Gene Family": "steelblue",
    "Resistance Mechanism": "deepskyblue",
    "uniprot": "red",
}

GENERAL_ARO_NODES = {
    "ARO:1000001",  # process or component of antibiotic biology or chemistry
    "ARO:1000002",  # mechanism of antibiotic resistance
    "ARO:1000003",  # antibiotic molecule
    "ARO:3000000",  # determinant of antibiotic resistance
}


# -------------------- helpers --------------------

def _pick_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_cols:
            return lower_cols[cand.lower()]
    return None


def load_mapping(map_file: str, accession: str) -> Tuple[str, str]:
    df = pd.read_csv(map_file, sep="\t")
    acc_col = _pick_column(df, ["UPKB", "UniProtKB_acc", "UniProtKB", "acc", "ACCESSION"]) or df.columns[0]
    aro_col = _pick_column(df, ["ARO Accession", "ARO", "ARO_accession"])
    if aro_col is None:
        raise ValueError("ARO accession column not found in mapping file")
    matches = df.loc[df[acc_col].astype(str) == accession]
    if matches.empty:
        raise ValueError(f"Accession {accession} not found in mapping file {map_file}")
    aro = str(matches[aro_col].iloc[0])
    return str(acc_col), aro


def _extract_subgraph(obo_path: str, aro: str) -> nx.MultiDiGraph:
    obo_graph: nx.MultiDiGraph = obonet.read_obo(obo_path)
    if aro not in obo_graph:
        raise ValueError(f"ARO {aro} not found in {obo_path}")
    descendants = nx.descendants(obo_graph, aro)
    descendants.add(aro)
    sub = obo_graph.subgraph(descendants).copy()
    out = nx.MultiDiGraph()
    out.add_nodes_from(sub.nodes(data=True))
    for u, v, key, data in sub.edges(keys=True, data=True):
        out.add_edge(u, v, key=key, **data)
    return out


def _label_from_synonym(synonym_list: Optional[List[str]]) -> Optional[str]:
    if not synonym_list:
        return None
    for syn in synonym_list:
        if "CARD_Short_Name" in syn:
            parts = syn.split("\"")
            if len(parts) >= 3:
                return parts[1]
    return None


def _wrap(text: str, n: int) -> str:
    words = text.split()
    lines = []
    current: List[str] = []
    for w in words:
        current.append(w)
        if len(" ".join(current)) >= n:
            lines.append(" ".join(current))
            current = []
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


# -------------------- variants --------------------

def add_variants(card_json: str, aro: str, graph: nx.MultiDiGraph, colors: Dict[str, str]) -> None:
    with open(card_json, "r") as fh:
        data = json.load(fh)

    aro_no_prefix = aro.split(":")[-1]

    for entry in data.values():
        if not isinstance(entry, dict):
            continue
        acc_val = str(entry.get("ARO_accession"))
        if acc_val not in {aro, aro_no_prefix}:
            continue
        if entry.get("model_type") != "protein variant model":
            continue

        variant_root = "SNPs"
        param_desc = entry.get("model_param", {}).get("snp", {}).get("param_description", "")
        graph.add_node(
            variant_root,
            name="SNPs",
            label="SNPs",
            title=param_desc,
            group="card",
            color=colors.get("card", "blue"),
            sources=["card.json"],
            category="variant",
        )
        graph.add_edge(aro, variant_root, label=entry.get("model_type", "variant"))

        snps = entry.get("model_param", {}).get("snp", {}).get("param_value", {})
        for snp in snps.values():
            graph.add_node(
                snp,
                name=snp,
                label=snp,
                title=snp,
                group="card",
                color=colors.get("card", "blue"),
                sources=["card.json"],
                category="variant",
            )
            graph.add_edge(
                variant_root,
                snp,
                label=entry.get("model_param", {}).get("snp", {}).get("param_type", "snp"),
            )


# -------------------- graph build --------------------

def build_card_graph(
    accession: str,
    map_file: str,
    obo_file: str,
    card_json: str,
    categories_file: str,
    colors: Dict[str, str],
    remove_general: bool = True,
    aro_override: Optional[str] = None,
) -> Tuple[nx.MultiDiGraph, str]:
    aro = aro_override or load_mapping(map_file, accession)[1]
    graph = _extract_subgraph(obo_file, aro)

    cat_df = pd.read_csv(categories_file, sep="\t")
    cat_map = dict(zip(cat_df[cat_df.columns[1]], cat_df[cat_df.columns[0]]))

    antibiotic_nodes = set()
    for src, tgt, key in graph.edges(keys=True):
        graph.edges[src, tgt, key]["label"] = key
        if key == "confers_resistance_to_antibiotic":
            antibiotic_nodes.add(tgt)

    for node, data in graph.nodes(data=True):
        syn = data.get("synonym")
        label = _label_from_synonym(syn) or data.get("name", node)
        title = f"{node}: {data.get('name', '')}; {data.get('def', '')}"

        group = "card"
        color = colors.get("card", "blue")
        category = None
        sources = set()

        if node in cat_map:
            category = cat_map[node]
            color = colors.get(category, color)
            sources.add("aro_categories.tsv")

        if node in antibiotic_nodes:
            category = category or "Antibiotic"
            color = colors.get("Antibiotic", color)
            sources.add("aro.obo")

        sources.add("aro.obo")

        graph.nodes[node].update(
            {
                "name": data.get("name", node),
                "label": label,
                "title": title,
                "group": group,
                "color": color,
                "category": category,
                "sources": sorted(sources),
            }
        )

        if "synonym" in graph.nodes[node]:
            del graph.nodes[node]["synonym"]

    add_variants(card_json, aro, graph, colors)

    if remove_general:
        for node in list(graph.nodes()):
            if node in GENERAL_ARO_NODES and node in graph:
                graph.remove_node(node)

    return graph, aro


def attach_uniprot_node(graph: nx.MultiDiGraph, accession: str, aro: str, colors: Dict[str, str]) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    G.add_node(
        accession,
        name=accession,
        label=accession,
        title=accession,
        group="uniprot",
        color=colors.get("uniprot", "red"),
        category=None,
        sources=["input"],
    )
    G = nx.union(G, graph)
    G.add_edge(accession, aro, label="is")
    return G


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


def apply_category_colors(graph: nx.MultiDiGraph, colors: Dict[str, str]) -> None:
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


# -------------------- payload --------------------

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


def to_payload(graph: nx.MultiDiGraph, aro_root: str, accession: str, include_uniprot: bool) -> Dict:
    if include_uniprot:
        graph = graph.copy()
        graph.add_node(accession, name=accession, label=accession, title=accession, group="uniprot", sources=["input"])
        graph.add_edge(accession, aro_root, label="is")

    nodes = []
    for nid, data in graph.nodes(data=True):
        nodes.append({"id": nid, **{k: v for k, v in data.items()}})

    edges = []
    for src, tgt, data in graph.edges(data=True):
        edges.append({"source": src, "target": tgt, **{k: v for k, v in data.items()}})

    return {"uniprot": accession, "aro_root": aro_root, "nodes": nodes, "edges": edges}


# -------------------- render --------------------

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


# -------------------- trace --------------------

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
