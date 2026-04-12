"""출력 파일명 생성 유틸."""

from __future__ import annotations

import re
import unicodedata

_WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
}


def sanitize_title_for_filename(title: str, max_len: int = 80) -> str:
    """Windows-safe 제목 문자열 생성."""
    text = unicodedata.normalize("NFKC", title or "").strip()
    # Windows 금지 문자/제어문자 제거
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", text)
    text = re.sub(r"\s+", " ", text).strip().rstrip(".")

    if not text:
        text = "video"

    if text.lower() in _WINDOWS_RESERVED:
        text = f"{text}_video"

    if len(text) > max_len:
        text = text[:max_len].rstrip()

    return text


def build_video_filename(title: str) -> str:
    """주제/타이틀 기반 최종 mp4 파일명."""
    safe = sanitize_title_for_filename(title).replace(" ", "_")
    return f"{safe}.mp4"
