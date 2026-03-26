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
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Default inputs (edit if your paths differ)
MAP_FILE = Path("/home/tunstall/amr/map_tsv/CARD-UniProt-Mapping.tsv")
OBO_FILE = Path("/home/tunstall/amr/databases/card/ontology/aro.obo")
CARD_JSON = Path("/home/tunstall/amr/databases/card/data/card.json")
CATEGORIES = Path("/home/tunstall/amr/databases/card/data/aro_categories.tsv")

ACCESSION = os.environ.get("CARD_ACCESSION", "Q182T3")
OUTDIR = Path(os.environ.get("CARD_OUTDIR", str(Path.home() / "card_output"))).expanduser()


def main() -> None:
    cmd = [
        "python",
        str(ROOT / "cli.py"),
        "from-api-json",
        "--api-mode",
        "create",
        "--accession",
        ACCESSION,
        "--map-file",
        str(MAP_FILE),
        "--obo-file",
        str(OBO_FILE),
        "--card-json",
        str(CARD_JSON),
        "--categories-file",
        str(CATEGORIES),
        "--outdir",
        str(OUTDIR),
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
