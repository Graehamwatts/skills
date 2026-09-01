#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape.py — safety wrapper around ScrapeGraphAI for Graeham's workspace.

Extraction ONLY (SmartScraperGraph). The code-generating graphs are banned:
CodeGeneratorGraph executes LLM-generated Python via exec() with no real
sandbox (RCE via prompt injection from a hostile page). Do not "improve" this
wrapper by exposing them.

Usage:
    python scrape.py "https://example.com" "every product name and price"
    python scrape.py URL PROMPT --schema '{"items": [{"name": "str", "price": "str"}]}'
    python scrape.py URL PROMPT --out results.json --model claude|openai
"""

import argparse
import json
import os
import re
import sys

# Telemetry off BEFORE the library is imported (rule 4 in SKILL.md).
os.environ["SCRAPEGRAPHAI_TELEMETRY_ENABLED"] = "false"

# Source fence (rule 3 in SKILL.md). Domains whose ToS forbid automated access.
BLOCKED = re.compile(
    r"(linkedin\.com|instagram\.com|tiktok\.com|facebook\.com|fb\.com|"
    r"loopnet\.com|threads\.net|x\.com|twitter\.com)",
    re.IGNORECASE,
)


def build_config(model_choice: str) -> dict:
    if model_choice == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            sys.exit("OPENAI_API_KEY not set. Set it in the environment (never hardcode).")
        llm = {"api_key": key, "model": "openai/gpt-5-mini"}
    else:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            sys.exit("ANTHROPIC_API_KEY not set. Set it in the environment (never hardcode).")
        llm = {"api_key": key, "model": "anthropic/claude-haiku-4-5-20251001"}
    return {
        "llm": llm,
        "verbose": False,
        "headless": True,
    }


def main():
    ap = argparse.ArgumentParser(description="Plain-English web extraction (safe wrapper)")
    ap.add_argument("url", help="Page to extract from (public, ToS-compatible sources only)")
    ap.add_argument("prompt", help="What to extract, in plain English")
    ap.add_argument("--schema", default=None, help="Optional JSON shape hint for the output")
    ap.add_argument("--out", default=None, help="Write JSON result to this file")
    ap.add_argument("--model", default="claude", choices=["claude", "openai"])
    args = ap.parse_args()

    if BLOCKED.search(args.url):
        sys.exit(
            "BLOCKED by the source fence (SKILL.md rule 3): this domain's terms forbid "
            "automated access. Pick a public, ToS-compatible source instead."
        )

    from scrapegraphai.graphs import SmartScraperGraph  # extraction-only graph

    prompt = args.prompt
    if args.schema:
        prompt += "\nReturn the result as JSON matching this shape: " + args.schema

    graph = SmartScraperGraph(
        prompt=prompt,
        source=args.url,
        config=build_config(args.model),
    )
    result = graph.run()

    text = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("written:", args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
