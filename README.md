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

See `NOTE.txt` for mapping-count details. 
The current mapping contains 4494 unique UniProt + ARO pairs from 4496 mapping rows, 
 including 14 UniProt accessions with more than one distinct ARO mapping 
 and 2 exact duplicate UniProt + ARO rows.

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
python -m venv ~/my_envs/cardvis_env
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

To generate one graph payload for each unique UniProt + ARO mapping, run:

```bash
bash generate_all_mock_payloads.sh
```

The expected output pattern is:

```text
card_api_data/ARO<NUMBER>_<ACCESSION>.json
```

After this step, `card_api_data/` acts as a local mock CARD API dataset for the mapped UniProt accessions. The script processes 4494 unique UniProt + ARO pairs, skips existing JSON files so it can be safely rerun, and passes the row-specific ARO to `run_extract_card_subgraph.py`.

If an accession fails, the script continues and logs the failed UniProt accession, ARO, and CARD URL to:

```text
card_api_data/generation_failures.tsv
```

## 3. Render One Mock API Payload
Use `run_render_kg.py` to render one generated JSON payload:

```bash
python run_render_kg.py \
  --accession Q182T3 \
  --aro-id ARO:3007637 \
  --subgraph-json card_api_data/ARO3007637_Q182T3.json \
  --outdir demo_html \
  --formats pyvis \
  --theme light
```

This reads the local mock API response and writes an interactive graph:

```text
demo_html/ARO3007637_Q182T3.html
```

To open the demo graph in Firefox browser:
```
firefox demo_html/ARO3007637_Q182T3.html
```

*NOTE: 
`--accession` and `--aro-id` are both required so rendering is explicit if one UniProt accession has multiple CARD ARO mappings. In these demo commands, keep `--subgraph-json` explicit because the JSON input is in `card_api_data/` while the HTML output is written to `demo_html/`.
    `--subgraph-json` if is omitted, the renderer derives the JSON path from `--outdir`, `--aro-id`, and `--accession`, for example:

```text
card_api_data/ARO3007637_Q182T3.json
```

The renderer checks that the CLI accession and ARO match the JSON payload fields `uniprot` and `aro_root`.

## OPTIONAL/Debug Outputs for ```run_render_kg.py```

`--trace` writes a debug CSV for inspecting nodes, edges, labels, categories, colours, and sources.
`--trace-json` writes a fully styled debug JSON snapshot. These debug outputs are optional and are not required for frontend rendering.
Debug outputs use the same ARO/accession basename, for example `trace_ARO3007637_Q182T3.csv`, so they remain unambiguous if one UniProt accession has multiple CARD ARO mappings.


## 4. Generate Static Demo HTML Graphs for All CARD-UP mappings
```bash
bash generate_all_html.sh
```

The JSON files in `card_api_data/` are the mock API responses. The HTML files in `demo_html/` are static PyVis outputs for local demo/review.

The script uses the light theme and writes:

```text
demo_html/ARO<NUMBER>_<ACCESSION>.html
```
This is optional. The JSON files in `card_api_data/` are the mock API responses. The HTML files in `demo_html/` are only for local demo/review.
It prints progress as it runs, and if rendering fails for a payload, the script continues and logs the failed accession, ARO, and JSON path to:

```text
demo_html/render_failures.tsv
```

**TODO for real CARD/API integration:**

- [ ] CARD provides an API endpoint that returns the JSON graph payload for a UniProt accession and ARO ID.
- [ ] The frontend fetches that JSON payload directly from the CARD API.
- [ ] The frontend converts the JSON `nodes` and `edges` into its graph component state.
- [ ] The frontend renders the graph dynamically in the browser DOM.
- [ ] The frontend does not depend on pre-generated static PyVis HTML files from `demo_html/`.

## Code Layout

`run_extract_card_subgraph.py` generates one mock API payload from local CARD files.

`generate_all_mock_payloads.sh` generates all mock API JSON payloads from `mock_api_inputs/CARD-UniProt-Mapping.tsv` into `card_api_data/`.

`run_render_kg.py` renders one generated payload as an interactive PyVis HTML graph.

`generate_all_html.sh` renders all generated JSON payloads from `card_api_data/` into light-theme HTML graphs in `demo_html/`.

`src/card_vis_extract.py` contains mapping lookup, CARD subgraph extraction, variant/SNP enrichment, and payload creation.

`src/card_vis_render.py` contains category colouring, label/title wrapping, PyVis rendering, and debug trace export.

## Examples To Try

Open a generated demo graph directly in Firefox:

```bash
firefox demo_html/ARO3007637_Q182T3.html
firefox demo_html/ARO3003373_A6T5M6.html
firefox demo_html/ARO3000263_P0ACH7.html
```

## What The Graph Shows

Each graph shows one UniProt accession and one CARD ARO mapping. The UniProt node links to the mapped CARD ARO term, then expands into related CARD ontology terms such as resistance mechanisms, AMR gene families, drug classes, antibiotics, and variant/SNP nodes where available.

Node colours indicate category:

- Red: UniProt accession
- Blue: general CARD/ARO term
- Purple: antibiotic
- Medium purple: drug class
- Steel blue: AMR gene family
- Light blue: resistance mechanism
- Orange: variant/SNP node

Edges show CARD relationships such as `is_a`, `confers_resistance_to_antibiotic`, and `confers_resistance_to_drug_class`.

Larger nodes have more incoming connections in the rendered graph, so node size is a visual cue for how connected a term is within that payload.


** Summary of Outstanding issues / tasks:**

- [ ] CARD to provide the API endpoint for graph payloads.
- [ ] CARD to provide reciprocal links with UniProt.
- [ ] Frontend team to help reconfigure/render the graph on the fly using D3, JavaScript, or another frontend graph library.
