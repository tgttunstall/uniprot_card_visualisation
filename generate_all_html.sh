#!/usr/bin/env bash
set -u

mkdir -p demo_html
rm -f demo_html/render_failures.tsv

total=$(ls card_api_data/ARO*.json 2>/dev/null | wc -l)
i=0

if [ "$total" -eq 0 ]; then
  printf 'No mock API JSON payloads found in card_api_data/ARO*.json\n'
  exit 1
fi

for json_file in card_api_data/ARO*.json; do
  i=$((i + 1))

  base=$(basename "$json_file" .json)
  aro_number=${base%%_*}
  accession=${base#*_}
  aro_id="ARO:${aro_number#ARO}"
  html_file="demo_html/${base}.html"

  printf '[%s/%s] Rendering %s -> %s\n' "$i" "$total" "$json_file" "$html_file"

  if python run_render_kg.py \
    --accession "$accession" \
    --aro-id "$aro_id" \
    --subgraph-json "$json_file" \
    --outdir demo_html \
    --formats pyvis \
    --theme light; then
    printf '[%s/%s] OK %s\n' "$i" "$total" "$base"
  else
    printf '[%s/%s] FAILED %s\n' "$i" "$total" "$base"
    printf '%s\t%s\t%s\n' "$accession" "$aro_id" "$json_file" >> demo_html/render_failures.tsv
  fi
done

printf 'Generated HTML graphs: '
ls demo_html/ARO*.html 2>/dev/null | wc -l

if [ -f demo_html/render_failures.tsv ]; then
  printf 'Failures: '
  wc -l < demo_html/render_failures.tsv
  printf 'Failure report: demo_html/render_failures.tsv\n'
else
  printf 'Failures: 0\n'
fi
