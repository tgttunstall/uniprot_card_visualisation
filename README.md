# UniProt CARD Visualisation

Lightweight Python scripts to build and render interactive CARD knowledge graphs for UniProt accessions. Two steps:

1) Extract a CARD subgraph to JSON: `run_extract_card_subgraph.py`
2) Render that JSON to an interactive PyVis HTML (optionally a trace CSV/JSON): `run_render_kg.py`

## Quick start

Create and activate the venv (already prepared):

```bash
python -m venv ~/myenvs/cardvis_env
source ~/myenvs/cardvis_env/bin/activate
pip install -r cardvis_env_requirements.txt
```

### 1) Extract subgraph from local CARD files

```bash
python run_extract_card_subgraph.py \
  --accession Q182T3 \
  --map-file ~/amr/map_tsv/CARD-UniProt-Mapping.tsv \
  --obo-file ~/amr/databases/card/ontology/aro.obo \
  --card-json ~/amr/databases/card/data/card.json \
  --categories-file ~/amr/databases/card/data/aro_categories.tsv \
  --outdir ~/card_output
```

- Uses `networkx` + `obonet` to read the ARO OBO, find descendants for the accession’s ARO, and attach variant/SNP nodes from `card.json`.
- Writes `~/card_output/card_subgraph_<ACC>.json` (nodes/edges payload; UniProt node is included).

### 2) Render the extracted payload

```bash
python run_render_kg.py \
  --accession Q182T3 \
  --subgraph-json ~/card_output/card_subgraph_Q182T3.json \
  --outdir ~/card_output \
  --formats pyvis \
  --theme dark \
  --trace
```

- Re-applies colouring, labels, and sizing for PyVis; outputs `~/card_output/Q182T3.html`.
- `--trace` writes `trace_<ACC>.csv`; `--trace-json` writes a styled JSON snapshot.
- Themes: `dark` (default) or `light`. Format: `pyvis` (HTML, interactive).

Defaults target `~/amr` bulk files and write to `~/card_output`; override paths via flags as needed.

## Provenance of code
- Core logic in `src/card_vis_extract.py` (mapping lookup, CARD subgraph extraction, variant/SNP enrichment, payload creation).
- Rendering/styling in `src/card_vis_render.py` (category colouring, label/title wrapping, PyVis rendering, trace export).
