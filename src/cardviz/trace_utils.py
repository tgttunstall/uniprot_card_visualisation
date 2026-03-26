from __future__ import annotations

import pandas as pd
import networkx as nx


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
