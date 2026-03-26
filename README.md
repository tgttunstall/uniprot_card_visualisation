# UniProt CARD Visualisation

Lightweight CLI to build interactive CARD knowledge graphs for UniProt accessions. Two modes:

- `from-local`: build directly from CARD flat files.
- `from-api-json`: either generate a mock API JSON (`create`) or render from an existing API-style JSON (`use`).

## Quick start

Create and activate the venv (already prepared):

```bash
python -m venv ~/myenvs/cardvis_env
source ~/myenvs/cardvis_env/bin/activate
pip install -r cardvis_env_requirements.txt
```

Run from local CARD files (dark theme, PyVis HTML + PNG):

```bash
python -m cli from-local \
  --accession Q182T3 \
  --map-file /home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv \
  --obo-file /home/tunstall/amr/databases/card/ontology/aro.obo \
  --card-json /home/tunstall/amr/databases/card/data/card.json \
  --categories-file /home/tunstall/amr/databases/card/data/aro_categories.tsv \
  --outdir ~/card_output \
  --formats pyvis,png \
  --theme dark
```

Generate mock API JSON then render from it (light theme example):

```bash
python -m cli from-api-json \
  --api-mode create \
  --accession Q182T3 \
  --map-file /home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv \
  --obo-file /home/tunstall/amr/databases/card/ontology/aro.obo \
  --card-json /home/tunstall/amr/databases/card/data/card.json \
  --categories-file /home/tunstall/amr/databases/card/data/aro_categories.tsv \
  --outdir ~/card_output \
  --formats pyvis \
  --theme light
```

Render from an existing API JSON:

```bash
python -m cli from-api-json \
  --api-mode use \
  --api-json-path ~/card_output/card_api_mock_Q182T3.json \
  --outdir ~/card_output \
  --formats pyvis
```

Add `--trace` to emit a `trace_<ACC>.csv` debug table per accession. Default output directory is `~/card_output` and is created if missing. Themes: `dark` (default) or `light`. Formats: `pyvis` (HTML, interactive) and optional `png` snapshot.

### Convenience runner

`run_card_kg.py` now only extracts the bare subgraph JSON (defaults to Q182T3) using local CARD files under `/home/tunstall/amr`. Override with env vars:

```bash
export CARD_ACCESSION=Q182T3
export CARD_OUTDIR=~/card_output
python run_card_kg.py
```

This produces `card_subgraph_<ACC>.json` in `CARD_OUTDIR`.

To render from an extracted JSON, use `render_card_kg.py` (assumes the JSON path):

```bash
export CARD_JSON_PATH=~/card_output/card_subgraph_Q182T3.json
export CARD_OUTDIR=~/card_output
python render_card_kg.py
```

This produces `<ACC>.html` (PyVis) and `<ACC>.png` in `CARD_OUTDIR`.

## Provenance of code
- Ported from `~/git/card_analysis/common_functions.py`: mapping lookup, CARD subgraph extraction (aro.obo), category colouring (aro_categories.tsv), antibiotic highlighting via `confers_resistance_to_antibiotic`, and variant/SNP enrichment from `card.json`.
- New in this repo: API-style payload conversion (`api_payload.py`), PyVis/PNG rendering with bundled options (`visualize.py`), CLI glue (`cardviz/cli.py` + top-level `cli.py`), trace export (`trace_utils.py`), and label/title wrapping/styling helpers in `graph_builder.py` for readability.
