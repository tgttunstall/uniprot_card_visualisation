# UniProt CARD Visualisation

Lightweight Python scripts to generate and render CARD antimicrobial resistance knowledge graph payloads for UniProt accessions.

## Background

CARD already provides UniProt-to-CARD mappings in:

```text
map_file/CARD-UniProt-Mapping.tsv
```

The mapping file contains 4497 lines: one header plus 4496 UniProt-to-CARD mappings. The key columns are `UPKB`, `ARO Accession`, `CARD Short Name`, `Resistance Mechanism`, and `CARD URL`.

This repo uses those existing CARD mappings to generate one CARD knowledge graph payload per UniProt accession.

## Integration Goal

The intended final integration is:

1. A frontend requests CARD graph data for a UniProt accession.
2. CARD provides an API endpoint returning the corresponding graph payload.
3. The frontend renders that payload as an interactive graph.

The CARD API endpoint and reciprocal CARD/UniProt links still need to be provided by CARD. Until that exists, this repo simulates the API response using local JSON files in:

```text
card_api_data/
```

Each generated file acts as a mock CARD API response:

```text
card_api_data/card_subgraph_<ACCESSION>.json
```

For example, `card_api_data/card_subgraph_Q182T3.json` is the mock API response for UniProt accession `Q182T3`.

## Setup

Create and activate the virtual environment, then install dependencies:

```bash
python -m venv ~/myenvs/cardvis_env
source ~/myenvs/cardvis_env/bin/activate
pip install -r cardvis_env_requirements.txt
```

The examples below assume the CARD bulk files are available at these paths:

```text
~/amr/databases/card/ontology/aro.obo
~/amr/databases/card/data/card.json
~/amr/databases/card/data/aro_categories.tsv
```

Override those paths in the commands if your local CARD files are somewhere else.

## 1. Generate One Mock API Payload

Use `run_extract_card_subgraph.py` to generate one JSON payload from local CARD files:

```bash
python run_extract_card_subgraph.py \
  --accession Q182T3 \
  --map-file map_file/CARD-UniProt-Mapping.tsv \
  --obo-file ~/amr/databases/card/ontology/aro.obo \
  --card-json ~/amr/databases/card/data/card.json \
  --categories-file ~/amr/databases/card/data/aro_categories.tsv \
  --outdir card_api_data \
  --include-uniprot
```

This writes:

```text
card_api_data/card_subgraph_Q182T3.json
```

This step simulates the CARD backend preparing the response that a future API endpoint would return.

## 2. Generate All Mock API Payloads

To generate one graph payload for each of the 4496 UniProt mappings, run this one-off loop from the repo root:

```bash
mkdir -p card_api_data

while IFS=$'\t' read -r upkb aro short_name rm_aro mechanism card_url; do
  if [ "$upkb" = "UPKB" ]; then
    continue
  fi

  if [ -z "$upkb" ]; then
    continue
  fi

  python run_extract_card_subgraph.py \
    --accession "$upkb" \
    --map-file map_file/CARD-UniProt-Mapping.tsv \
    --obo-file ~/amr/databases/card/ontology/aro.obo \
    --card-json ~/amr/databases/card/data/card.json \
    --categories-file ~/amr/databases/card/data/aro_categories.tsv \
    --outdir card_api_data \
    --include-uniprot
done < map_file/CARD-UniProt-Mapping.tsv
```

The expected output pattern is:

```text
card_api_data/card_subgraph_<ACCESSION>.json
```

After this step, `card_api_data/` acts as a local mock CARD API dataset for the mapped UniProt accessions.

To check how many payloads were generated:

```bash
ls card_api_data/card_subgraph_*.json | wc -l
```

## 3. Render One Mock API Payload

Use `run_render_kg.py` to render one generated JSON payload:

```bash
python run_render_kg.py \
  --accession Q182T3 \
  --subgraph-json card_api_data/card_subgraph_Q182T3.json \
  --outdir card_api_data \
  --formats pyvis \
  --theme dark
```

This reads the local mock API response and writes an interactive graph:

```text
card_api_data/Q182T3.html
```

This step simulates the frontend receiving `card_subgraph_Q182T3.json` from a future CARD API endpoint and rendering it.

## Debug Outputs

`--trace` writes a debug CSV for inspecting nodes, edges, labels, categories, colours, and sources:

```bash
python run_render_kg.py \
  --accession Q182T3 \
  --subgraph-json card_api_data/card_subgraph_Q182T3.json \
  --outdir card_api_data \
  --formats pyvis \
  --theme dark \
  --trace
```

`--trace-json` writes a fully styled debug JSON snapshot. These debug outputs are optional and are not required for frontend rendering.

## Code Layout

`run_extract_card_subgraph.py` generates one mock API payload from local CARD files.

`run_render_kg.py` renders one generated payload as an interactive PyVis HTML graph.

`src/card_vis_extract.py` contains mapping lookup, CARD subgraph extraction, variant/SNP enrichment, and payload creation.

`src/card_vis_render.py` contains category colouring, label/title wrapping, PyVis rendering, and debug trace export.
