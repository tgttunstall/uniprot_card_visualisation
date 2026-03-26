#!/usr/bin/env python
"""
Extract a bare CARD subgraph for a UniProt accession using the original CARD
files (mapping TSV, aro.obo, card.json, aro_categories.tsv). This is a minimal
data export: nodes and edges only, no added styling/colours.

Output JSON structure:
{
  "uniprot": "<ACC>",
  "aro_root": "<ARO>",
  "nodes": [ { "id", "name", "label", "def", "category", "group", "sources", "title" } ],
  "edges": [ { "source", "target", "label", "title" } ]
}

Example:
python extract_card_subgraph.py \
  --accession Q182T3 \
  --map-file /home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv \
  --obo-file /home/tunstall/amr/databases/card/ontology/aro.obo \
  --card-json /home/tunstall/amr/databases/card/data/card.json \
  --categories-file /home/tunstall/amr/databases/card/data/aro_categories.tsv \
  --out /home/tunstall/card_output/card_subgraph_Q182T3.json
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, Iterable, Optional, Tuple

import networkx as nx
import obonet
import pandas as pd


GENERAL_ARO_NODES = {
    "ARO:1000001",  # process or component of antibiotic biology or chemistry
    "ARO:1000002",  # mechanism of antibiotic resistance
    "ARO:1000003",  # antibiotic molecule
    "ARO:3000000",  # determinant of antibiotic resistance
}


def _pick_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_cols:
            return lower_cols[cand.lower()]
    return None


def load_mapping(map_file: str, accession: str) -> Tuple[str, str]:
    df = pd.read_csv(map_file, sep="\t")
    acc_col = _pick_column(df, ["UPKB", "UniProtKB_acc", "UniProtKB", "acc", "ACCESSION"])
    if acc_col is None:
        acc_col = df.columns[0]
    aro_col = _pick_column(df, ["ARO Accession", "ARO", "ARO_accession"])
    if aro_col is None:
        raise ValueError("ARO accession column not found in mapping file")

    matches = df.loc[df[acc_col].astype(str) == accession]
    if matches.empty:
        raise ValueError(f"Accession {accession} not found in mapping file {map_file}")

    aro = str(matches[aro_col].iloc[0])
    return acc_col, aro


def extract_subgraph(obo_path: str, aro: str) -> nx.MultiDiGraph:
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


def label_from_synonym(synonym_list):
    if not synonym_list:
        return None
    for syn in synonym_list:
        if "CARD_Short_Name" in syn:
            parts = syn.split("\"")
            if len(parts) >= 3:
                return parts[1]
    return None


def add_variants(card_json: str, aro: str, graph: nx.MultiDiGraph) -> None:
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
            sources=["card.json"],
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
                sources=["card.json"],
            )
            graph.add_edge(
                variant_root,
                snp,
                label=entry.get("model_param", {}).get("snp", {}).get("param_type", "snp"),
            )


def card_graph(accession: str, map_file: str, obo_file: str, card_json: str, categories_file: str, aro_override: str = None) -> Tuple[nx.MultiDiGraph, str]:
    if aro_override:
        aro = aro_override
    else:
        _, aro = load_mapping(map_file, accession)
    graph = extract_subgraph(obo_file, aro)

    cat_df = pd.read_csv(categories_file, sep="\t")
    cat_map = dict(zip(cat_df[cat_df.columns[1]], cat_df[cat_df.columns[0]]))

    antibiotic_nodes = set()
    for src, tgt, key in graph.edges(keys=True):
        graph.edges[src, tgt, key]["label"] = key
        if key == "confers_resistance_to_antibiotic":
            antibiotic_nodes.add(tgt)

    for node, data in graph.nodes(data=True):
        syn = data.get("synonym")
        label = label_from_synonym(syn) or data.get("name", node)
        title = f"{node}: {data.get('name', '')}; {data.get('def', '')}"

        group = "card"
        category = None
        sources = []

        if node in cat_map:
            category = cat_map[node]
            sources.append("aro_categories.tsv")

        if node in antibiotic_nodes:
            category = category or "Antibiotic"
            sources.append("aro.obo")

        sources.append("aro.obo")

        graph.nodes[node].update(
            {
                "name": data.get("name", node),
                "label": label,
                "title": title,
                "group": group,
                "category": category,
                "sources": sorted(set(sources)),
            }
        )

        if "synonym" in graph.nodes[node]:
            del graph.nodes[node]["synonym"]

    add_variants(card_json, aro, graph)

    for n in list(graph.nodes()):
        if n in GENERAL_ARO_NODES and n in graph:
            graph.remove_node(n)

    return graph, aro


def to_payload(graph: nx.MultiDiGraph, aro_root: str, accession: str, include_uniprot: bool) -> Dict:
    if include_uniprot:
        graph = graph.copy()
        graph.add_node(accession, name=accession, label=accession, title=accession, group="uniprot", sources=["input"])
        graph.add_edge(accession, aro_root, label="is")

    nodes = []
    for nid, data in graph.nodes(data=True):
        nodes.append({"id": nid, **{k: v for k, v in data.items() if k not in {}}})

    edges = []
    for src, tgt, data in graph.edges(data=True):
        edges.append({"source": src, "target": tgt, **{k: v for k, v in data.items() if k not in {}}})

    return {"uniprot": accession, "aro_root": aro_root, "nodes": nodes, "edges": edges}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract bare CARD subgraph as JSON")
    p.add_argument("--accession", required=True)
    p.add_argument("--aro-root", help="Override ARO root (skip mapping)")
    p.add_argument("--map-file", help="Mapping TSV (required unless --aro-root provided)")
    p.add_argument("--obo-file", required=True)
    p.add_argument("--card-json", required=True)
    p.add_argument("--categories-file", required=True)
    p.add_argument("--out", required=True, help="Output JSON path")
    p.add_argument("--include-uniprot", action="store_true", help="Include UniProt node and edge to ARO root")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    aro_override = args.aro_root
    if not aro_override and not args.map_file:
        raise SystemExit("--map-file is required unless --aro-root is provided")

    graph, aro = card_graph(
        accession=args.accession,
        map_file=args.map_file if args.map_file else "",
        obo_file=args.obo_file,
        card_json=args.card_json,
        categories_file=args.categories_file,
        aro_override=aro_override,
    )

    payload = to_payload(graph, aro_root=aro, accession=args.accession, include_uniprot=args.include_uniprot)

    out_path = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Wrote subgraph JSON to {out_path}")


if __name__ == "__main__":
    main()
