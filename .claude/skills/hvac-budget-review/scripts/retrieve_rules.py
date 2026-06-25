#!/usr/bin/env python3
"""Keyword-based rule retrieval for the HVAC budget-review skill.

Every rule already carries curated keywords, so this does plain lexical
matching against the case text instead of embeddings/vector search -
the corpus is small (~54 rules) and the matching needs to be exactly
reproducible across runs, not similarity-fuzzy.

Usage:
    retrieve_rules.py "<case text>" [--category history|material|roi|other|external|all] [--top N]
    retrieve_rules.py --list-categories
"""
import argparse
import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

CATEGORY_FILES = {
    "history": "historical_cases.json",
    "material": "material_list_rules.json",
    "roi": "roi_rules.json",
    "other": "other_rules.json",
    "external": "external_data.json",
}


def load_category(name):
    path = os.path.join(DATA_DIR, CATEGORY_FILES[name])
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score(record, text):
    hits = [kw for kw in record.get("keywords", []) if kw and kw.lower() in text.lower()]
    return hits


def search(text, categories, top_n):
    results = {}
    for cat in categories:
        records = load_category(cat)
        scored = []
        for r in records:
            hits = score(r, text)
            if hits:
                scored.append((len(hits), hits, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        results[cat] = scored[:top_n]
    return results


def format_results(results):
    lines = []
    any_hit = False
    for cat, scored in results.items():
        lines.append(f"## 類別: {cat}")
        if not scored:
            lines.append("(無匹配規則)")
            continue
        any_hit = True
        for n_hits, hits, r in scored:
            lines.append(f"- [{r['id']}] {r['title']}  (命中關鍵字: {', '.join(hits)})")
            lines.append(f"  判斷規則: {r['rule']}")
            if r.get("example"):
                lines.append(f"  範例: {r['example']}")
            lines.append(f"  建議處置: {r['disposition']}")
            if r.get("note"):
                lines.append(f"  備註: {r['note']}")
        lines.append("")
    if not any_hit:
        lines.append("*** 所有類別均未匹配到規則，請依 SKILL.md 的「未匹配規則」流程處理，不可憑印象自行判斷。 ***")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", help="案件文字（標題、設計說明、料單、效益計算等，越完整匹配越準）")
    parser.add_argument("--category", default="all", choices=list(CATEGORY_FILES) + ["all"])
    parser.add_argument("--top", type=int, default=5, help="每類別最多回傳幾筆 (預設 5)")
    parser.add_argument("--list-categories", action="store_true")
    args = parser.parse_args()

    if args.list_categories:
        for cat, fname in CATEGORY_FILES.items():
            records = load_category(cat)
            print(f"{cat}: {len(records)} 筆 ({fname})")
        return

    if not args.text:
        parser.error("請提供案件文字，或使用 --list-categories")

    categories = list(CATEGORY_FILES) if args.category == "all" else [args.category]
    results = search(args.text, categories, args.top)
    print(format_results(results))


if __name__ == "__main__":
    main()
