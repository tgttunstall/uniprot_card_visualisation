#!/usr/bin/env python
"""
Convenience runner for generating a CARD knowledge graph for a UniProt accession.

Defaults target the local CARD files under /home/tunstall/amr; adjust as needed or
override via environment variables.

Environment overrides:
  CARD_ACCESSION   (default: Q182T3)
  CARD_OUTDIR      (default: ~/card_output)
"""

from __future__ import annotations

import os
import subprocess


ROOT = os.path.dirname(os.path.abspath(__file__))

# Default inputs (edit if your paths differ)
MAP_FILE = "/home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv"
OBO_FILE = "/home/tunstall/amr/databases/card/ontology/aro.obo"
CARD_JSON = "/home/tunstall/amr/databases/card/data/card.json"
CATEGORIES = "/home/tunstall/amr/databases/card/data/aro_categories.tsv"

ACCESSION = os.environ.get("CARD_ACCESSION", "Q182T3")
OUTDIR = os.path.expanduser(os.environ.get("CARD_OUTDIR", os.path.join(os.path.expanduser("~"), "card_output")))


def main() -> None:
    cmd = [
        "python",
        os.path.join(ROOT, "cli.py"),
        "from-api-json",
        "--api-mode",
        "create",
        "--accession",
        ACCESSION,
        "--map-file",
        MAP_FILE,
        "--obo-file",
        OBO_FILE,
        "--card-json",
        CARD_JSON,
        "--categories-file",
        CATEGORIES,
        "--outdir",
        OUTDIR,
        "--formats",
        "pyvis,png",
        "--theme",
        "dark",
        "--trace",
    ]

    print("Running:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
