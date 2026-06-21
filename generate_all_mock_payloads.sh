#!/usr/bin/env bash
set -u

mkdir -p card_api_data
rm -f card_api_data/generation_failures.tsv

mapping_file="mock_api_inputs/CARD-UniProt-Mapping.tsv"

if [ ! -f "$mapping_file" ]; then
  printf 'Mapping file not found: %s\n' "$mapping_file"
  exit 1
fi

unique_pairs_file=$(mktemp)
trap 'rm -f "$unique_pairs_file"' EXIT

python - "$mapping_file" "$unique_pairs_file" <<'PY'
import csv
import sys
from collections import Counter, defaultdict

mapping_file = sys.argv[1]
unique_pairs_file = sys.argv[2]

rows = []
with open(mapping_file, newline="") as fh:
    reader = csv.DictReader(fh, delimiter="\t")
    for row in reader:
        upkb = row["UPKB"]
        aro = row["ARO Accession"]
        card_url = row.get("CARD URL", "")
        rows.append((upkb, aro, card_url))

pairs = [(upkb, aro) for upkb, aro, _ in rows]
pair_counts = Counter(pairs)
by_upkb = defaultdict(set)
for upkb, aro, _ in rows:
    by_upkb[upkb].add(aro)

seen = set()
unique_rows = []
for upkb, aro, card_url in rows:
    pair = (upkb, aro)
    if pair in seen:
        continue
    seen.add(pair)
    unique_rows.append((upkb, aro, card_url))

with open(unique_pairs_file, "w", newline="") as fh:
    writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
    writer.writerows(unique_rows)

multi = {upkb: sorted(aros) for upkb, aros in by_upkb.items() if len(aros) > 1}

print("Mapping summary:")
print(f"  mapping rows after header: {len(rows)}")
print(f"  unique UniProt accessions: {len(by_upkb)}")
print(f"  unique UniProt + ARO pairs: {len(unique_rows)}")
print(f"  exact duplicate UniProt + ARO rows: {len(rows) - len(unique_rows)}")
print(f"  UniProt accessions with multiple ARO mappings: {len(multi)}")
if multi:
    print("  multi-ARO UniProt accessions:")
    for upkb in sorted(multi):
        print(f"    {upkb}: {', '.join(multi[upkb])}")
PY

total=$(wc -l < "$unique_pairs_file")
i=0
generated=0
skipped=0
failed=0

while IFS=$'\t' read -r upkb aro card_url; do
  if [ -z "$upkb" ]; then
    continue
  fi

  i=$((i + 1))
  outfile="card_api_data/${aro//:/}_${upkb}.json"

  if [ -f "$outfile" ]; then
    skipped=$((skipped + 1))
    printf '[%s/%s] SKIP existing %s\n' "$i" "$total" "$outfile"
    continue
  fi

  printf '[%s/%s] Generating %s + %s -> %s\n' "$i" "$total" "$upkb" "$aro" "$outfile"

  if python run_extract_card_subgraph.py \
    --accession "$upkb" \
    --aro-root "$aro" \
    --map-file "$mapping_file" \
    --obo-file mock_api_inputs/aro.obo \
    --card-json mock_api_inputs/card.json \
    --categories-file mock_api_inputs/aro_categories.tsv \
    --outdir card_api_data \
    --include-uniprot; then
    generated=$((generated + 1))
    printf '[%s/%s] OK %s %s\n' "$i" "$total" "$upkb" "$aro"
  else
    failed=$((failed + 1))
    printf '[%s/%s] FAILED %s %s\n' "$i" "$total" "$upkb" "$aro"
    printf '%s\t%s\t%s\n' "$upkb" "$aro" "$card_url" >> card_api_data/generation_failures.tsv
  fi
done < "$unique_pairs_file"

printf 'Generated new payloads: %s\n' "$generated"
printf 'Skipped existing payloads: %s\n' "$skipped"
printf 'Failures: %s\n' "$failed"
printf 'Current payload files: '
ls card_api_data/ARO*.json 2>/dev/null | wc -l

if [ -f card_api_data/generation_failures.tsv ]; then
  printf 'Failure report: card_api_data/generation_failures.tsv\n'
fi
