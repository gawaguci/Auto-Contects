"""Claude API + 웹 검색 또는 로컬 기본 주제로 트렌드 주제 추천."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

try:
    import anthropic
except Exception:  # pragma: no cover - optional dependency fallback
    anthropic = None
from dotenv import load_dotenv

import config


@dataclass
class TopicItem:
    """추천 주제 1건."""
    index: int
    title: str          # 30자 이내
    hook: str           # 첫 3초 후크, 20자 이내
    trend: str          # 트렌드 이유 한 줄
    keywords: list[str] = field(default_factory=list)


# 시스템 프롬프트
_SYSTEM_PROMPT = (
    "유튜브 콘텐츠 트렌드 분석가.\n"
    "반드시 웹 검색으로 최신 트렌드를 조사한 후 추천하라.\n"
    "최종 답변은 JSON 배열만 반환하고, 다른 텍스트는 절대 포함하지 마라."
)


def _load_user_prompt(category: dict) -> str:
    """프롬프트 템플릿 로드 후 카테고리 정보 삽입."""
    template_path = config.TEMPLATES_DIR / "topic_search_prompt.txt"
    template = template_path.read_text(encoding="utf-8")
    return template.format(
        category_name=category["name"],
        search_query=category["search_query"],
    )


def _extract_json_array(text: str) -> list[dict]:
    """텍스트에서 JSON 배열 추출. 직접 파싱 실패 시 정규식 fallback."""
    text = text.strip()

    # 마크다운 코드블록 제거
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # 직접 JSON 파싱 시도
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 정규식으로 JSON 배열 패턴 추출
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(f"JSON 배열 파싱 실패. 원문:\n{text[:500]}")


def _parse_response(response) -> list[dict]:
    """Claude 응답에서 마지막 text 블록의 JSON 추출."""
    last_text = ""
    for block in response.content:
        if block.type == "text":
            last_text = block.text

    if not last_text:
        raise ValueError("Claude 응답에 텍스트 블록이 없습니다.")

    return _extract_json_array(last_text)


def _local_topics(category: dict) -> list[TopicItem]:
    """API 없이 사용할 로컬 기본 주제 5개."""
    presets = {
        "심리학": [
            "확증편향이 판단을 망치는 순간",
            "손실회피가 선택을 왜곡하는 이유",
            "가짜 자신감이 만드는 의사결정 오류",
            "관계를 망치는 투사 심리 패턴",
            "습관을 바꾸는 행동 트리거 설계",
        ],
        "역사 충격": [
            "교과서 밖 조선의 반전 기록",
            "전쟁의 승패를 바꾼 숨은 변수",
            "왕조를 흔든 정책 실패의 진실",
            "역사적 오해가 반복되는 이유",
            "한 장의 문서가 바꾼 권력 지형",
        ],
        "뇌과학": [
            "집중력이 무너지는 뇌의 메커니즘",
            "도파민 루프를 끊는 실전 루틴",
            "수면 부족이 기억력을 훔치는 방식",
            "스트레스와 전두엽 성능 저하",
            "학습 효율을 올리는 뇌 사용법",
        ],
        "한국사 X파일": [
            "조선의 숨겨진 정보전 이야기",
            "독립운동 네트워크의 실전 전략",
            "기록에서 사라진 사건의 단서",
            "왕실 의사결정의 비공개 변수",
            "교과서가 짧게 다룬 큰 사건",
        ],
        "돈의 심리학": [
            "손실회피가 수익률을 깎는 방식",
            "앵커링 편향과 소비 패턴",
            "부자 습관의 반복 구조",
            "투자에서 감정을 분리하는 법",
            "복리를 망치는 행동 실수 3가지",
        ],
        "경제 다큐": [
            "금리 변화가 가계에 전파되는 경로",
            "인플레이션 체감이 커지는 구조",
            "환율 급변 시 시장 반응 패턴",
            "공급망 충격과 가격 전이",
            "불황 국면에서 살아남는 전략",
        ],
    }

    titles = presets.get(category["name"], [
        f"{category['name']} 핵심 트렌드 1",
        f"{category['name']} 핵심 트렌드 2",
        f"{category['name']} 핵심 트렌드 3",
        f"{category['name']} 핵심 트렌드 4",
        f"{category['name']} 핵심 트렌드 5",
    ])

    topics: list[TopicItem] = []
    for i, title in enumerate(titles[:5], start=1):
        topics.append(
            TopicItem(
                index=i,
                title=title,
                hook=f"{i}분 안에 핵심 정리",
                trend=f"{category['name']} 관심 키워드 상승 흐름 반영",
                keywords=[w for w in re.split(r"[\\s,]+", title) if len(w) >= 2][:4],
            )
        )
    return topics


def generate_topics(category: dict, max_retries: int = 2) -> list[TopicItem]:
    """카테고리 기반 트렌드 주제 5개 추천.

    Args:
        category: config.CATEGORIES 항목 하나
        max_retries: API 에러 시 최대 재시도 횟수

    Returns:
        TopicItem 5개 리스트
    """
    # .env 로드
    load_dotenv(config.PROJECT_ROOT / ".env")

    if not config.allow_claude_api():
        print("  로컬 AI 모드 - API 주제 생성을 사용하지 않습니다.")
        return _local_topics(category)

    api_key = config.get_api_key().strip()
    if not api_key:
        print("  ANTHROPIC_API_KEY 없음 - 로컬 기본 주제 생성 사용")
        return _local_topics(category)

    if anthropic is None:
        raise RuntimeError("anthropic 패키지가 없어 API 주제 생성을 실행할 수 없습니다.")

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _load_user_prompt(category)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=config.MODEL_NAME,
                max_tokens=2000,
                system=_SYSTEM_PROMPT,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,
                }],
                messages=[{"role": "user", "content": user_prompt}],
            )

            items = _parse_response(response)

            # TopicItem 리스트로 변환
            topics = []
            for i, item in enumerate(items[:5], start=1):
                topics.append(TopicItem(
                    index=i,
                    title=item.get("title", ""),
                    hook=item.get("hook", ""),
                    trend=item.get("trend", ""),
                    keywords=item.get("keywords", []),
                ))

            return topics

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                print(f"  주제 생성 실패 (시도 {attempt + 1}/{max_retries + 1}): {e}")
                print(f"  {wait}초 후 재시도...")
                time.sleep(wait)

    raise RuntimeError(f"주제 생성 최종 실패: {last_error}")
