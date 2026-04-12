"""Web UI용 스크립트 미리보기 생성 + 프롬프트 정보."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import config
import pipeline.script_gen as script_gen


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _resolve_template_file(category: dict, version: str) -> Path:
    if version == "shorts":
        category_template = category.get("script_template")
        fallback = "shorts_script_prompt.txt"
    else:
        category_template = category.get("longform_script_template")
        fallback = "longform_script_prompt.txt"

    if category_template:
        candidate = config.TEMPLATES_DIR / category_template
        if candidate.exists():
            return candidate

    return config.TEMPLATES_DIR / fallback


class _TopicObj:
    def __init__(self, title: str):
        self.title = title
        self.index = 1
        self.hook = title
        self.trend = ""
        self.keywords = []


def main() -> int:
    _configure_stdio()

    parser = argparse.ArgumentParser(description="스크립트 미리보기 생성")
    parser.add_argument("--category", type=int, required=True)
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--type", type=str, default="shorts", choices=["shorts", "longform"])
    parser.add_argument("--language", type=str, default="ko", choices=["ko", "en"])
    args = parser.parse_args()

    category = next((c for c in config.CATEGORIES if c["id"] == args.category), None)
    if not category:
        print(json.dumps({"error": f"invalid category id: {args.category}"}, ensure_ascii=False))
        return 2

    topic = _TopicObj(args.topic)
    script = script_gen.generate_script(topic, category, args.type, language=args.language)

    template_path = _resolve_template_file(category, args.type)
    template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else ""
    rendered_prompt = script_gen._load_user_prompt(topic, category, args.type, args.language)

    payload = {
        "script": {
            "version": script.version,
            "title": script.title,
            "category": script.category,
            "totalDuration": script.total_duration,
            "cta": script.cta,
            "scenes": [
                {
                    "index": s.index,
                    "duration": s.duration,
                    "narration": s.narration,
                    "subtitle": s.subtitle,
                    "imagePrompt": s.image_prompt,
                    "bgColor": s.bg_color,
                    "videoQuery": s.video_query,
                }
                for s in script.scenes
            ],
        },
        "prompt": {
            "system": script_gen._SYSTEM_PROMPT,
            "template_file": template_path.name,
            "template_text": template_text,
            "rendered_prompt": rendered_prompt,
        },
    }

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())