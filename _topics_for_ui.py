"""Web UI용 카테고리 주제 목록 조회."""

from __future__ import annotations

import argparse
import json
import sys

import config
from pipeline.topic_gen import generate_topics


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main() -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="카테고리별 주제 5개 생성")
    parser.add_argument("--category", type=int, required=True, help="카테고리 ID")
    args = parser.parse_args()

    category = next((c for c in config.CATEGORIES if c["id"] == args.category), None)
    if not category:
        print(json.dumps({"error": f"invalid category id: {args.category}"}, ensure_ascii=False))
        return 2

    topics = generate_topics(category)
    payload = [
        {
            "index": t.index,
            "title": t.title,
            "hook": t.hook,
            "trend": t.trend,
            "keywords": t.keywords,
        }
        for t in topics
    ]
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
