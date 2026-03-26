#!/usr/bin/env python
"""
Render a CARD KG from a previously extracted subgraph JSON (PyVis + PNG).

Assumes the JSON came from extract_card_subgraph.py (nodes/edges only). This
script applies category colours and styling via cardviz.cli use-mode.

Env overrides:
  CARD_JSON_PATH (path to subgraph JSON)
  CARD_OUTDIR    (default: ~/card_output)
  CARD_ACCESSION (used for output filenames if payload lacks id)
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

JSON_PATH = os.environ.get("CARD_JSON_PATH", os.path.join(os.path.expanduser("~"), "card_output", "card_subgraph_Q182T3.json"))

OUTDIR = os.path.expanduser(os.environ.get("CARD_OUTDIR", os.path.join(os.path.expanduser("~"), "card_output")))
ACCESSION = os.environ.get("CARD_ACCESSION")


def main() -> None:
    render_cmd = [
        "python",
        "-m",
        "cardviz.cli",
        "from-api-json",
        "--api-mode",
        "use",
        "--api-json-path",
        JSON_PATH,
        "--outdir",
        OUTDIR,
        "--formats",
        "pyvis,png",
        "--theme",
        "dark",
    ]
    if ACCESSION:
        render_cmd.extend(["--accession", ACCESSION])

    print("Running (render):")
    print(" ".join(render_cmd))
    env = os.environ.copy()
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run(render_cmd, check=True, env=env)


if __name__ == "__main__":
    main()
