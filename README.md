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
  --formats pyvis \
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

Add `--trace` to emit a `trace_<ACC>.csv` debug table per accession. Default output directory is `~/card_output` and is created if missing. Themes: `dark` (default) or `light`. Format: `pyvis` (HTML, interactive).

### Convenience runner

`run_card_kg.py` is a unified runner (no env vars needed):

- Extract only:
  ```bash
  python run_card_kg.py --step extract \
    --accession Q182T3 \
    --map-file /home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv \
    --obo-file /home/tunstall/amr/databases/card/ontology/aro.obo \
    --card-json /home/tunstall/amr/databases/card/data/card.json \
    --categories-file /home/tunstall/amr/databases/card/data/aro_categories.tsv \
    --outdir ~/card_output \
    --include-uniprot
  ```

- Render only (from an existing subgraph):
  ```bash
  python run_card_kg.py --step render \
    --accession Q182T3 \
    --subgraph-json ~/card_output/card_subgraph_Q182T3.json \
    --outdir ~/card_output \
  --formats pyvis \
  --theme dark
  ```

- Do both (default step): same as extract + render combined; omit `--step` to run both in sequence.

Defaults target `/home/tunstall/amr` bulk files and write to `~/card_output/card_subgraph_<ACC>.json`; override paths via flags as needed.

CLI entrypoint: `python src/cli.py ...` (you can also do `PYTHONPATH=./src python -m cli ...`).

Run scripts:
- Extract: `python run_extract_card_subgraph.py --accession Q182T3 --include-uniprot`
- Render (PyVis HTML): `python run_render_kg.py --accession Q182T3 --subgraph-json ~/card_output/card_subgraph_Q182T3.json`

## Provenance of code
- Ported from `~/git/card_analysis/common_functions.py`: mapping lookup, CARD subgraph extraction (aro.obo), category colouring (aro_categories.tsv), antibiotic highlighting via `confers_resistance_to_antibiotic`, and variant/SNP enrichment from `card.json`.
- New in this repo: API-style payload conversion (`api_payload.py`), PyVis/PNG rendering with bundled options (`visualize.py`), CLI glue (`cardviz/cli.py` + top-level `cli.py`), trace export (`trace_utils.py`), and label/title wrapping/styling helpers in `graph_builder.py` for readability.
