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
    "variant": "darkorange",
}

GENERAL_ARO_NODES = {
    "ARO:1000001",
    "ARO:1000002",
    "ARO:1000003",
    "ARO:3000000",
}


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
        variant_color = colors.get("variant", colors.get("card", "blue"))
        graph.add_node(
            variant_root,
            name="SNPs",
            label="SNPs",
            title=param_desc,
            group="card",
            color=variant_color,
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
                color=variant_color,
                sources=["card.json"],
                category="variant",
            )
            graph.add_edge(
                variant_root,
                snp,
                label=entry.get("model_param", {}).get("snp", {}).get("param_type", "snp"),
            )


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
