# UniProt CARD Visualisation

Lightweight Python scripts to generate and render CARD antimicrobial resistance knowledge graph payloads for UniProt accessions.

## Background

CARD already provides UniProt-to-CARD mappings as a TSV. A copy of it exists in this repo:

```text
mock_api_inputs/CARD-UniProt-Mapping.tsv
```

The mapping file contains 4497 lines: one header plus 4496 UniProt-to-CARD mappings. The key columns are `UPKB`, `ARO Accession`, `CARD Short Name`, `Resistance Mechanism`, and `CARD URL`.

This repo uses those existing CARD mappings to generate one CARD knowledge graph payload per UniProt accession.

This workflow currently treats each row in `CARD-UniProt-Mapping.tsv` as one graph payload. If a UniProt accession maps to more than one CARD ARO entry, each mapping should produce a separate payload. Including both IDs in the filename keeps those cases unambiguous, for example `ARO3000001_P12345.json` and `ARO3000002_P12345.json`.

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
card_api_data/ARO<NUMBER>_<ACCESSION>.json
```

For example, `card_api_data/ARO3007637_Q182T3.json` is the mock API response for UniProt accession `Q182T3` mapped to `ARO:3007637`.

## Setup

Create and activate the virtual environment, then install dependencies:

```bash
python -m venv ~/myenvs/cardvis_env
source ~/myenvs/cardvis_env/bin/activate
pip install -r cardvis_env_requirements.txt
```

The examples below use repo-local copies of the CARD mapping and bulk files:

```text
mock_api_inputs/CARD-UniProt-Mapping.tsv
mock_api_inputs/aro.obo
mock_api_inputs/card.json
mock_api_inputs/aro_categories.tsv
```

These local files are only needed to generate mock API payloads while the CARD API endpoint does not exist.

## 1. Generate One Mock API Payload

Use `run_extract_card_subgraph.py` to generate one JSON payload from local CARD files:

```bash
python run_extract_card_subgraph.py \
  --accession Q182T3 \
  --map-file mock_api_inputs/CARD-UniProt-Mapping.tsv \
  --obo-file mock_api_inputs/aro.obo \
  --card-json mock_api_inputs/card.json \
  --categories-file mock_api_inputs/aro_categories.tsv \
  --outdir card_api_data \
  --include-uniprot
```

This writes:

```text
card_api_data/ARO3007637_Q182T3.json
```

**IMPORTANT:** This step simulates the CARD backend preparing the response that a future API endpoint would return. Once CARD provides that API, the frontend will not need `run_extract_card_subgraph.py` or any of the local files in `mock_api_inputs/`; it will consume the API response directly.

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
    --map-file mock_api_inputs/CARD-UniProt-Mapping.tsv \
    --obo-file mock_api_inputs/aro.obo \
    --card-json mock_api_inputs/card.json \
    --categories-file mock_api_inputs/aro_categories.tsv \
    --outdir card_api_data \
    --include-uniprot
done < mock_api_inputs/CARD-UniProt-Mapping.tsv
```

The expected output pattern is:

```text
card_api_data/ARO<NUMBER>_<ACCESSION>.json
```

After this step, `card_api_data/` acts as a local mock CARD API dataset for the mapped UniProt accessions.

To check how many payloads were generated:

```bash
ls card_api_data/ARO*.json | wc -l
```

## 3. Render One Mock API Payload

Use `run_render_kg.py` to render one generated JSON payload:

```bash
python run_render_kg.py \
  --accession Q182T3 \
  --aro-id ARO:3007637 \
  --subgraph-json card_api_data/ARO3007637_Q182T3.json \
  --outdir card_api_data \
  --formats pyvis \
  --theme dark
```

This reads the local mock API response and writes an interactive graph:

```text
card_api_data/ARO3007637_Q182T3.html
```

This step simulates the frontend receiving `ARO3007637_Q182T3.json` from a future CARD API endpoint and rendering it.

`--accession` and `--aro-id` are both required so rendering is explicit if one UniProt accession has multiple CARD ARO mappings. If `--subgraph-json` is omitted, the renderer expects the file at:

```text
card_api_data/ARO3007637_Q182T3.json
```

The renderer checks that the CLI accession and ARO match the JSON payload fields `uniprot` and `aro_root`.

## Debug Outputs

`--trace` writes a debug CSV for inspecting nodes, edges, labels, categories, colours, and sources:

```bash
python run_render_kg.py \
  --accession Q182T3 \
  --aro-id ARO:3007637 \
  --subgraph-json card_api_data/ARO3007637_Q182T3.json \
  --outdir card_api_data \
  --formats pyvis \
  --theme dark \
  --trace
```

`--trace-json` writes a fully styled debug JSON snapshot. These debug outputs are optional and are not required for frontend rendering.

Debug outputs use the same ARO/accession basename, for example `trace_ARO3007637_Q182T3.csv`, so they remain unambiguous if one UniProt accession has multiple CARD ARO mappings.

## Code Layout

`run_extract_card_subgraph.py` generates one mock API payload from local CARD files.

`run_render_kg.py` renders one generated payload as an interactive PyVis HTML graph.

`src/card_vis_extract.py` contains mapping lookup, CARD subgraph extraction, variant/SNP enrichment, and payload creation.

`src/card_vis_render.py` contains category colouring, label/title wrapping, PyVis rendering, and debug trace export.
