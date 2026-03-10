#!/usr/bin/env python3
"""
Merge tools and positive_indicators from learning_strategies_v1.json
into the new learning_strategies.json, and enrich with precise tool names.
"""
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "api" / "app" / "config"
V1_PATH = CONFIG_DIR / "learning_strategies_v1.json"
NEW_PATH = CONFIG_DIR / "learning_strategies.json"

# --- Load both files ---
with open(V1_PATH) as f:
    v1_strategies = json.load(f)
with open(NEW_PATH) as f:
    new_strategies = json.load(f)

# Build v1 lookup (handle visualisation → visualization mapping)
v1_lookup = {}
for s in v1_strategies:
    sid = s["strategy_id"]
    if sid == "visualisation":
        v1_lookup["visualization"] = s
    v1_lookup[sid] = s

# --- Enriched tools: v1 originals + precise modern tools ---
ENRICHED_TOOLS = {
    "rehearsal_mnemonics": [
        "flashcards", "lists", "memory aids",
        "Anki", "Quizlet", "Brainscape"
    ],
    "practice_testing": [
        "practice tests", "flashcards", "question banks",
        "Kahoot", "Quizlet", "past exam papers"
    ],
    "repetition_over_time": [
        "flashcard apps", "study schedules",
        "Anki (spaced repetition)", "Leitner box system", "RemNote"
    ],
    "reviewing_records": [
        "notes", "textbooks",
        "OneNote", "Notion", "Evernote", "Google Docs"
    ],
    "highlighting_underlining": [
        "highlighters", "pens",
        "GoodNotes", "Notability", "PDF annotation (Adobe Acrobat)"
    ],
    "organization": [
        "mind maps", "concept maps",
        "XMind", "MindMeister", "Notion", "Obsidian", "CmapTools"
    ],
    "keeping_records": [
        "notebooks", "learning logs",
        "Notion", "OneNote", "bullet journal", "Google Keep"
    ],
    "visualization": [
        "sketches", "diagrams",
        "Miro", "Excalidraw", "Canva", "draw.io", "whiteboards"
    ],
    "teaching_preparing_to_teach": [
        "slides", "study groups",
        "PowerPoint", "Google Slides", "screen recording (Loom, OBS)"
    ],
    "self_explanation": [
        "notes", "inner speech",
        "journal / notebook", "voice recorder", "dictation apps"
    ],
    "goal_setting_planning": [
        "to-do lists", "study plans",
        "Todoist", "Trello", "Google Calendar", "Notion"
    ],
    "self_evaluating_regulation": [
        "checklists", "feedback notes",
        "rubrics", "self-assessment forms", "learning analytics dashboards"
    ],
    "environmental_structuring": [
        "quiet rooms", "headphones",
        "noise-cancelling headphones", "Freedom (website blocker)",
        "Cold Turkey", "desk organizer"
    ],
    "self_consequences": [
        "rewards", "break activities",
        "Habitica", "Streaks (habit tracker)", "reward journal"
    ],
    "seeking_social_assistance": [
        "forums", "study groups",
        "Discord", "WhatsApp study groups", "Stack Exchange",
        "university forums / Moodle"
    ],
    "seeking_selecting_information": [
        "internet", "libraries",
        "Google Scholar", "YouTube tutorials", "Khan Academy",
        "Wikipedia", "library databases"
    ],
    "time_management": [
        "timers", "calendars",
        "Forest (Pomodoro app)", "Pomofocus", "Google Calendar",
        "Toggl Track"
    ],
    "other": [],
}

# --- Merge ---
for strategy in new_strategies:
    sid = strategy["strategy_id"]

    # 1. Positive indicators from v1
    v1 = v1_lookup.get(sid)
    if v1 and v1.get("positive_indicators"):
        strategy["positive_indicators"] = v1["positive_indicators"]

    # 2. Enriched tools (v1 originals + precise additions)
    if sid in ENRICHED_TOOLS:
        strategy["tools"] = ENRICHED_TOOLS[sid]
    elif v1 and v1.get("tools"):
        strategy["tools"] = v1["tools"]

# --- Write back ---
with open(NEW_PATH, "w", encoding="utf-8") as f:
    json.dump(new_strategies, f, indent=2, ensure_ascii=False)

print(f"✅  Merged tools and positive_indicators into {NEW_PATH.name}")
for s in new_strategies:
    t = len(s.get("tools", []))
    p = len(s.get("positive_indicators", []))
    print(f"  {s['strategy_id']:40s}  tools={t}  indicators={p}")
