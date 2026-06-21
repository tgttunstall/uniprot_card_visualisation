#!/usr/bin/env bash
set -u

mkdir -p card_api_data
rm -f card_api_data/generation_failures.tsv

mapping_file="mock_api_inputs/CARD-UniProt-Mapping.tsv"

if [ ! -f "$mapping_file" ]; then
  printf 'Mapping file not found: %s\n' "$mapping_file"
  exit 1
fi

total=$(($(wc -l < "$mapping_file") - 1))
i=0

while IFS=$'\t' read -r upkb aro short_name rm_aro mechanism card_url; do
  if [ "$upkb" = "UPKB" ]; then
    continue
  fi

  if [ -z "$upkb" ]; then
    continue
  fi

  i=$((i + 1))
  outfile="card_api_data/${aro//:/}_${upkb}.json"

  printf '[%s/%s] Generating %s -> %s\n' "$i" "$total" "$upkb" "$outfile"

  if python run_extract_card_subgraph.py \
    --accession "$upkb" \
    --map-file "$mapping_file" \
    --obo-file mock_api_inputs/aro.obo \
    --card-json mock_api_inputs/card.json \
    --categories-file mock_api_inputs/aro_categories.tsv \
    --outdir card_api_data \
    --include-uniprot; then
    printf '[%s/%s] OK %s\n' "$i" "$total" "$upkb"
  else
    printf '[%s/%s] FAILED %s %s\n' "$i" "$total" "$upkb" "$aro"
    printf '%s\t%s\t%s\n' "$upkb" "$aro" "$card_url" >> card_api_data/generation_failures.tsv
  fi
done < "$mapping_file"

printf 'Generated payloads: '
ls card_api_data/ARO*.json 2>/dev/null | wc -l

if [ -f card_api_data/generation_failures.tsv ]; then
  printf 'Failures: '
  wc -l < card_api_data/generation_failures.tsv
  printf 'Failure report: card_api_data/generation_failures.tsv\n'
else
  printf 'Failures: 0\n'
fi
