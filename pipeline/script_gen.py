"""Claude API 또는 로컬 템플릿으로 장면별 스크립트 생성."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field

try:
    import anthropic
except Exception:  # pragma: no cover - optional dependency fallback
    anthropic = None

import config
from pipeline.topic_gen import TopicItem


@dataclass
class Scene:
    """영상 한 장면."""
    index: int
    duration: float       # 초 단위
    narration: str        # TTS용 나레이션
    subtitle: str         # 15자 이내 핵심 자막
    image_prompt: str     # 영문 이미지 프롬프트
    bg_color: str         # hex 색상코드
    video_query: str = "" # 스톡 영상/이미지 검색 키워드 (영문)
    role: str = ""        # hook/problem/numbered/stat/solution/closing


@dataclass
class Script:
    """전체 스크립트."""
    version: str          # "shorts" | "longform"
    title: str
    category: str
    scenes: list[Scene] = field(default_factory=list)
    total_duration: float = 0.0
    cta: str = ""


# 버전별 설정
_VERSION_CONFIG = {
    "shorts": {
        "template": "shorts_script_prompt.txt",  # 카테고리 템플릿 없을 때 폴백
        "expected_scenes": 10,
        "min_duration": 85,
        "max_duration": 95,
    },
    "longform": {
        "template": "longform_script_prompt.txt",
        "expected_scenes": 12,
        "min_duration": 480,
        "max_duration": 600,
    },
}

_SYSTEM_PROMPT = (
    "유튜브 영상 스크립트 전문 작가.\n"
    "시청자를 끌어들이는 매력적인 스크립트를 작성한다.\n"
    "지시된 JSON 형식만 반환하고, 다른 텍스트는 절대 포함하지 마라."
)


def _language_instruction(language: str) -> str:
    if language == "en":
        return (
            "중요: 모든 결과 텍스트(title, narration, subtitle, cta)는 반드시 영어로 작성하라. "
            "자막(subtitle)은 15자 이내의 짧은 영어 문구로 작성하라."
        )
    return (
        "중요: 모든 결과 텍스트(title, narration, subtitle, cta)는 반드시 한국어로 작성하라. "
        "자막(subtitle)은 15자 이내의 짧은 한국어 문구로 작성하라."
    )


def _load_user_prompt(topic: TopicItem, category: dict, version: str, language: str) -> str:
    """프롬프트 템플릿 로드. shorts는 카테고리별 전용 템플릿 우선 사용."""
    # 버전별 카테고리 전용 템플릿 우선 사용
    if version == "shorts":
        category_template = category.get("script_template")
    else:  # longform
        category_template = category.get("longform_script_template")
    if category_template:
        template_path = config.TEMPLATES_DIR / category_template
        if template_path.exists():
            template = template_path.read_text(encoding="utf-8")
            base_prompt = template.format(
                category_name=category["name"],
                category_emoji=category["emoji"],
                topic_title=topic.title,
                topic_hook=topic.hook,
                keywords=", ".join(topic.keywords),
            )
            return f"{base_prompt}\n\n[언어 지시]\n{_language_instruction(language)}"
    # 폴백: 기존 공통 템플릿
    vc = _VERSION_CONFIG[version]
    template_path = config.TEMPLATES_DIR / vc["template"]
    template = template_path.read_text(encoding="utf-8")
    base_prompt = template.format(
        category_name=category["name"],
        category_emoji=category["emoji"],
        topic_title=topic.title,
        topic_hook=topic.hook,
        keywords=", ".join(topic.keywords),
    )
    return f"{base_prompt}\n\n[언어 지시]\n{_language_instruction(language)}"


def _extract_json_object(text: str) -> dict:
    """텍스트에서 JSON 객체 추출."""
    text = text.strip()

    # 마크다운 코드블록 제거
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # 직접 파싱
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # 정규식 fallback
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(f"JSON 객체 파싱 실패. 원문:\n{text[:500]}")


def _adjust_durations(scenes: list[Scene], min_dur: float, max_dur: float) -> None:
    """전체 duration이 범위를 벗어나면 비례 조정."""
    total = sum(s.duration for s in scenes)
    if total < min_dur:
        ratio = min_dur / total
        for s in scenes:
            s.duration = round(s.duration * ratio, 1)
    elif total > max_dur:
        ratio = max_dur / total
        for s in scenes:
            s.duration = round(s.duration * ratio, 1)


def _resolve_scene_settings(category: dict, version: str) -> tuple[int, float, float, list[dict]]:
    """버전/카테고리별 씬 설정과 duration 범위 반환."""
    vc = _VERSION_CONFIG[version]

    if version == "longform":
        scene_format = category.get("longform_scene_format")
    else:
        scene_format = category.get("scene_format")

    if scene_format:
        expected_scenes = int(scene_format["total_scenes"])
        target_dur = float(scene_format["duration_seconds"])
        min_duration = target_dur - 3
        max_duration = target_dur + 3
        structure = scene_format.get("structure", [])
    else:
        expected_scenes = int(vc["expected_scenes"])
        min_duration = float(vc["min_duration"])
        max_duration = float(vc["max_duration"])
        structure = []

    return expected_scenes, min_duration, max_duration, structure


def _topic_keywords(topic: TopicItem) -> list[str]:
    """주제에서 키워드 후보 추출."""
    kws = [k.strip() for k in (topic.keywords or []) if str(k).strip()]
    if kws:
        return kws

    # 키워드가 없으면 제목에서 추출
    from_title = [w.strip() for w in re.split(r"[,\s/]+", topic.title) if len(w.strip()) >= 2]
    if from_title:
        return from_title[:8]

    return ["핵심"]


def _trim_subtitle(text: str, limit: int = 15) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1] + "…"


def _role_for_index(idx: int, total: int) -> str:
    if idx == 1:
        return "hook"
    if idx == total:
        return "closing"
    if idx >= total - 2:
        return "solution"
    if idx % 4 == 0:
        return "stat"
    return "numbered"


def _local_subtitle(role: str, idx: int, keyword: str, language: str) -> str:
    if language == "en":
        if role == "hook":
            return _trim_subtitle("Key Hook")
        if role == "problem":
            return _trim_subtitle("Core Problem")
        if role == "numbered":
            return _trim_subtitle(f"Point {idx}")
        if role == "solution":
            return _trim_subtitle("Action Step")
        if role == "stat":
            return _trim_subtitle("Key Data")
        if role == "quote":
            return _trim_subtitle("Main Quote")
        if role == "closing":
            return _trim_subtitle("Summary")
        return _trim_subtitle(keyword or "Key")

    if role == "hook":
        return _trim_subtitle("핵심 훅")
    if role == "problem":
        return _trim_subtitle("문제 원인")
    if role == "numbered":
        return _trim_subtitle(f"{idx}번째 포인트")
    if role == "solution":
        return _trim_subtitle("실행 방법")
    if role == "stat":
        return _trim_subtitle("핵심 데이터")
    if role == "quote":
        return _trim_subtitle("핵심 인용")
    if role == "closing":
        return _trim_subtitle("핵심 정리")
    return _trim_subtitle(keyword or "핵심")


def _local_narration(role: str, idx: int, topic: TopicItem, keyword: str, language: str) -> str:
    """로컬 모드용 기본 나레이션 문장."""
    if language == "en":
        if role == "hook":
            return f"{topic.title}. Here are the key points in under two minutes."
        if role == "problem":
            return f"Many people repeat the same mistake around {topic.title}. Let's break down why."
        if role == "numbered":
            return f"Point {idx}: {keyword}. This factor can change the outcome significantly."
        if role == "solution":
            return f"The practical action is simple. Start a routine focused on {keyword} today."
        if role == "stat":
            return f"Data shows the gap related to {keyword} keeps widening over time."
        if role == "quote":
            return "\"The key is a repeatable principle.\" Let's apply that to this topic."
        if role == "closing":
            return f"In short, {topic.title} is about consistently executing workable principles."
        return f"A key element of {topic.title} is {keyword}."

    if role == "hook":
        return f"{topic.title}. 지금부터 핵심만 빠르게 정리합니다."
    if role == "problem":
        return f"많은 사람이 {topic.title}에서 같은 실수를 반복합니다. 원인을 먼저 짚어보겠습니다."
    if role == "numbered":
        return f"{idx}번째 포인트는 {keyword}입니다. 이 요소가 결과를 크게 바꿉니다."
    if role == "solution":
        return f"실천 방법은 단순합니다. 오늘부터 {keyword} 중심으로 루틴을 적용해 보세요."
    if role == "stat":
        return f"데이터를 보면 {keyword}와 관련된 격차가 꾸준히 커집니다. 작은 차이가 누적됩니다."
    if role == "quote":
        return "\"핵심은 반복 가능한 원칙이다.\" 이 기준으로 지금 내용을 다시 정리해 보겠습니다."
    if role == "closing":
        return f"정리하면 {topic.title}의 핵심은 실행 가능한 원칙을 꾸준히 지키는 것입니다."
    return f"{topic.title}의 핵심 요소는 {keyword}입니다."


_CATEGORY_EN = {
    "심리학": "psychology",
    "역사 충격": "history",
    "뇌과학": "neuroscience",
    "한국사 X파일": "korean history",
    "돈의 심리학": "money psychology",
    "경제 다큐": "economy",
}


def _local_image_prompt(category_name: str, role: str, topic_title: str, keyword: str) -> str:
    cat_en = _CATEGORY_EN.get(category_name, "documentary")
    return (
        f"{cat_en} cinematic visual, {topic_title}, {keyword}, {role} moment, "
        "dramatic lighting, vertical 9:16, no text, no letters"
    )


def _local_video_query(category_name: str, role: str, keyword: str) -> str:
    cat_en = _CATEGORY_EN.get(category_name, "documentary")
    return f"{cat_en} {role} {keyword}".strip()


def _role_color(role: str) -> str:
    role_colors = {
        "hook": "#1a2a4a",
        "problem": "#2a1f2e",
        "numbered": "#1f2f2a",
        "solution": "#24422a",
        "stat": "#213145",
        "quote": "#2b2637",
        "closing": "#172738",
    }
    return role_colors.get(role, "#1a1a2e")


def _generate_script_local(
    topic: TopicItem,
    category: dict,
    version: str,
    expected_scenes: int,
    min_duration: float,
    max_duration: float,
    structure: list[dict],
    language: str,
) -> Script:
    """API 없이 scene_format 기반 로컬 스크립트 생성."""
    keywords = _topic_keywords(topic)
    avg_duration = (min_duration + max_duration) / 2.0
    fallback_scene_duration = round(avg_duration / max(expected_scenes, 1), 1)

    scenes: list[Scene] = []
    for idx in range(1, expected_scenes + 1):
        if idx <= len(structure):
            row = structure[idx - 1]
            role = str(row.get("role", _role_for_index(idx, expected_scenes)))
            duration = float(row.get("duration", fallback_scene_duration))
        else:
            role = _role_for_index(idx, expected_scenes)
            duration = fallback_scene_duration

        keyword = keywords[(idx - 1) % len(keywords)]
        scenes.append(
            Scene(
                index=idx,
                duration=duration,
                narration=_local_narration(role, idx, topic, keyword, language),
                subtitle=_local_subtitle(role, idx, keyword, language),
                image_prompt=_local_image_prompt(category["name"], role, topic.title, keyword),
                bg_color=_role_color(role),
                video_query=_local_video_query(category["name"], role, keyword),
                role=role,
            )
        )

    _adjust_durations(scenes, min_duration, max_duration)
    total_duration = round(sum(s.duration for s in scenes), 1)

    return Script(
        version=version,
        title=topic.title,
        category=category["name"],
        scenes=scenes,
        total_duration=total_duration,
        cta="Subscribe for the next video." if language == "en" else "구독하고 다음 영상도 확인하세요.",
    )


def _generate_script_via_claude_cli(
    topic: TopicItem,
    category: dict,
    version: str,
    expected_scenes: int,
    min_duration: float,
    max_duration: float,
    language: str,
) -> Script | None:
    """claude --print CLI를 subprocess로 호출해 고품질 스크립트 생성.

    USE_CLAUDE_API=0 환경에서 Claude Code 자체(저)를 AI로 활용.
    프롬프트는 stdin으로 전달해 Windows 인코딩 문제 완전 우회.
    실패 시 None 반환 → 호출자가 local fallback 처리.
    """
    import shutil
    import subprocess as _sp

    claude_bin = shutil.which("claude")
    if not claude_bin:
        return None

    user_prompt = _load_user_prompt(topic, category, version, language)
    full_prompt = f"{_SYSTEM_PROMPT}\n\n{user_prompt}"

    try:
        si = None
        cf = 0
        if os.name == "nt":
            si = _sp.STARTUPINFO()
            si.dwFlags |= _sp.STARTF_USESHOWWINDOW
            si.wShowWindow = _sp.SW_HIDE
            cf = _sp.CREATE_NO_WINDOW

        # 프롬프트를 stdin으로 전달 — CLI 인자로 넘기면 Windows cp949에서 깨짐
        result = _sp.run(
            [claude_bin, "--print", "--output-format", "text"],
            input=full_prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            startupinfo=si,
            creationflags=cf,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        if result.returncode != 0 or not result.stdout.strip():
            sys.stdout.buffer.write(
                f"  claude CLI 스크립트 생성 실패 (rc={result.returncode})\n".encode("utf-8")
            )
            return None

        output = result.stdout.strip()

        # 마크다운 코드블록 제거
        output = re.sub(r"^```(?:json)?\s*", "", output)
        output = re.sub(r"\s*```$", "", output)
        output = output.strip()

        # JSON 추출
        data = _extract_json_object(output)

        scenes = []
        total_scenes = len(data.get("scenes", []))
        for item in data.get("scenes", []):
            idx = item.get("index", len(scenes) + 1)
            role = str(item.get("role", _role_for_index(idx, total_scenes)))
            scenes.append(Scene(
                index=idx,
                duration=float(item.get("duration", 6)),
                narration=item.get("narration", ""),
                subtitle=_trim_subtitle(item.get("subtitle", "")),
                image_prompt=item.get("image_prompt", ""),
                bg_color=item.get("bg_color", _role_color(role)),
                video_query=item.get("video_query", ""),
                role=role,
            ))

        if not scenes:
            return None

        _adjust_durations(scenes, min_duration, max_duration)

        return Script(
            version=version,
            title=data.get("title", topic.title),
            category=category["name"],
            scenes=scenes,
            total_duration=round(sum(s.duration for s in scenes), 1),
            cta=data.get("cta", "구독하고 다음 영상도 확인하세요." if language == "ko" else "Subscribe for more."),
        )

    except Exception as e:
        sys.stdout.buffer.write(
            f"  claude CLI 스크립트 생성 예외: {e}\n".encode("utf-8", errors="replace")
        )
        return None


def generate_script(
    topic: TopicItem,
    category: dict,
    version: str = "shorts",
    max_retries: int = 2,
    language: str = "ko",
) -> Script:
    """주제 기반 스크립트 생성.

    Args:
        topic: 선택된 주제
        category: 카테고리 설정
        version: "shorts" 또는 "longform"
        max_retries: 최대 재시도 횟수

    Returns:
        Script 객체
    """
    expected_scenes, min_duration, max_duration, structure = _resolve_scene_settings(category, version)

    if not config.allow_claude_api():
        print("  로컬 AI 모드 - Claude Code CLI로 스크립트 생성 시도...")
        script = _generate_script_via_claude_cli(
            topic=topic,
            category=category,
            version=version,
            expected_scenes=expected_scenes,
            min_duration=min_duration,
            max_duration=max_duration,
            language=language,
        )
        if script is not None:
            print(f"  Claude Code CLI 스크립트 생성 완료: {len(script.scenes)}장면")
            return script
        print("  Claude Code CLI 실패 - 로컬 템플릿으로 폴백")
        return _generate_script_local(
            topic=topic,
            category=category,
            version=version,
            expected_scenes=expected_scenes,
            min_duration=min_duration,
            max_duration=max_duration,
            structure=structure,
            language=language,
        )

    api_key = config.get_api_key().strip()
    if not api_key:
        print("  ANTHROPIC_API_KEY 없음 - 로컬 템플릿 스크립트 생성 사용")
        return _generate_script_local(
            topic=topic,
            category=category,
            version=version,
            expected_scenes=expected_scenes,
            min_duration=min_duration,
            max_duration=max_duration,
            structure=structure,
            language=language,
        )

    if anthropic is None:
        raise RuntimeError("anthropic 패키지가 없어 API 스크립트 생성을 실행할 수 없습니다.")

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _load_user_prompt(topic, category, version, language)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=config.MODEL_NAME,
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # 마지막 text 블록에서 JSON 추출
            last_text = ""
            for block in response.content:
                if block.type == "text":
                    last_text = block.text

            data = _extract_json_object(last_text)

            # Scene 리스트 구성
            scenes = []
            for item in data.get("scenes", []):
                scenes.append(Scene(
                    index=item.get("index", len(scenes) + 1),
                    duration=float(item.get("duration", 5)),
                    narration=item.get("narration", ""),
                    subtitle=_trim_subtitle(item.get("subtitle", "")),
                    image_prompt=item.get("image_prompt", ""),
                    bg_color=item.get("bg_color", "#1a1a2e"),
                    video_query=item.get("video_query", ""),
                ))

            if not scenes:
                raise RuntimeError("Claude 응답에 scenes가 없습니다.")

            # duration 범위 조정
            _adjust_durations(scenes, min_duration, max_duration)

            total_duration = sum(s.duration for s in scenes)

            return Script(
                version=version,
                title=data.get("title", topic.title),
                category=category["name"],
                scenes=scenes,
                total_duration=round(total_duration, 1),
                cta=data.get("cta", ""),
            )

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                print(f"  스크립트 생성 실패 (시도 {attempt + 1}/{max_retries + 1}): {e}")
                print(f"  {wait}초 후 재시도...")
                time.sleep(wait)

    raise RuntimeError(f"스크립트 생성 최종 실패: {last_error}")
