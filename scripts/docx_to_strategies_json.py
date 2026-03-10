#!/usr/bin/env python3
"""
Convert LearningStrategies_draft.docx → learning_strategies.json

Reads the first table from the Word document and produces the same JSON
structure used by the RAG strategy-embedding pipeline.

Usage
-----
    cd srl-chat
    poetry run python scripts/docx_to_strategies_json.py

Outputs
-------
    api/app/config/learning_strategies.json
"""

import json
import pathlib
import re
import sys

try:
    from docx import Document
except ImportError:
    sys.exit("python-docx is required.  Install with:  pip install python-docx")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCX_PATH = PROJECT_ROOT / "docs" / "LearningStrategies_draft.docx"
OUTPUT_PATH = PROJECT_ROOT / "backend" / "config" / "learning_strategies.json"

# ---------------------------------------------------------------------------
# Static metadata that cannot be derived from the docx table
# ---------------------------------------------------------------------------
# strategy_id is derived from the strategy name (snake_case).
# zimmerman_phase is assigned per strategy based on the existing taxonomy.
PHASE_MAP: dict[str, str] = {
    "rehearsal_mnemonics":        "performance",
    "practice_testing":           "performance",
    "repetition_over_time":       "performance",
    "reviewing_records":          "performance",
    "highlighting_underlining":   "performance",
    "organization":               "performance",
    "keeping_records":            "performance",
    "visualization":              "performance",
    "teaching_preparing_to_teach": "performance",
    "self_explanation":           "performance",
    "goal_setting_planning":      "forethought",
    "self_evaluating_regulation": "self_reflection",
    "environmental_structuring":  "performance",
    "self_consequences":          "self_reflection",
    "seeking_social_assistance":  "performance",
    "seeking_selecting_information": "performance",
    "time_management":            "forethought",
    "other":                      "other",
}

# Mapping from strategy number (as it appears in the docx) to a stable
# snake_case strategy_id.  This keeps IDs consistent across versions.
NUMBER_TO_ID: dict[int, str] = {
    1:  "rehearsal_mnemonics",
    2:  "practice_testing",
    3:  "repetition_over_time",
    4:  "reviewing_records",
    5:  "highlighting_underlining",
    6:  "organization",
    7:  "keeping_records",
    8:  "visualization",
    9:  "teaching_preparing_to_teach",
    10: "self_explanation",
    11: "goal_setting_planning",
    12: "self_evaluating_regulation",
    13: "environmental_structuring",
    14: "self_consequences",
    15: "seeking_social_assistance",
    16: "seeking_selecting_information",
    17: "time_management",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Strip and normalise whitespace."""
    return text.strip()


def _split_lines(text: str) -> list[str]:
    """Split newline-separated cell contents into a clean list of strings."""
    return [line.strip() for line in text.strip().split("\n") if line.strip()]


def _extract_number(strategy_col: str) -> int | None:
    """Extract the leading number from e.g. '1. Rehearsal and mnemonic strategies'."""
    m = re.match(r"(\d+)\.", strategy_col.strip())
    return int(m.group(1)) if m else None


def _extract_name(strategy_col: str) -> str:
    """Extract the name after the number prefix."""
    return re.sub(r"^\d+\.\s*", "", strategy_col.strip())


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def convert(docx_path: pathlib.Path = DOCX_PATH) -> list[dict]:
    doc = Document(str(docx_path))
    table = doc.tables[0]  # First table contains the updated strategies

    strategies: list[dict] = []

    for row in table.rows[1:]:  # skip header row
        cells = [c.text for c in row.cells]
        category_text = _clean(cells[0])
        strategy_text = _clean(cells[1])
        description   = _clean(cells[2])
        methods_text  = _clean(cells[3])

        # "Other" row has no number
        number = _extract_number(strategy_text)
        if number is None:
            strategy_id = "other"
            name = "Other / Externally Regulated"
        else:
            strategy_id = NUMBER_TO_ID.get(number)
            if strategy_id is None:
                print(f"WARNING: Unknown strategy number {number} — skipping")
                continue
            name = _extract_name(strategy_text)

        phase = PHASE_MAP.get(strategy_id, "performance")
        methods = _split_lines(methods_text)

        entry = {
            "strategy_id": strategy_id,
            "name": name,
            "zimmerman_phase": phase,
            "category": category_text,
            "definitions": [description] if description else [],
            "student_phrases": methods[:5],   # first 5 methods as student phrases
            "methods": methods,
            "tools": [],                      # not in the docx — fill manually if needed
            "positive_indicators": [],        # not in the docx — fill manually if needed
            "literature": ["Zimmerman & Martinez-Pons (1986)"],
        }
        strategies.append(entry)

    return strategies


def main():
    if not DOCX_PATH.exists():
        sys.exit(f"Docx not found: {DOCX_PATH}")

    strategies = convert()
    print(f"Extracted {len(strategies)} strategies from {DOCX_PATH.name}")

    for s in strategies:
        print(f"  {s['strategy_id']:35s}  {s['name']}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(strategies, f, indent=2, ensure_ascii=False)

    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
