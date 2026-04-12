"""씬별 배경 이미지 조달.

우선순위:
  1. Gemini 이미지 생성 (GEMINI_API_KEY 있을 때, google-genai SDK)
  2. Pexels 스톡 이미지 (PEXELS_API_KEY 있을 때)
  3. Pixabay 스톡 이미지 (PIXABAY_API_KEY 있을 때)

캐시:
  - Gemini: output/gemini_cache/{hash}.png
  - Pexels/Pixabay: output/stock_cache/{hash}.jpg
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import urllib.parse
import urllib.request
import json
from pathlib import Path

from dotenv import load_dotenv

import config

load_dotenv(config.PROJECT_ROOT / ".env", override=False)

_STOCK_CACHE = config.OUTPUT_DIR / "stock_cache"
_GEMINI_CACHE = config.OUTPUT_DIR / "gemini_cache"
_PEXELS_API = "https://api.pexels.com/v1/search"
_PIXABAY_API = "https://pixabay.com/api/"

# 429 쿼터 소진 시 나머지 씬 시도 중단 플래그
_gemini_quota_exhausted = False


def _sanitize(query: str) -> str:
    q = re.sub(r"[^a-zA-Z0-9_\-]", "_", query.strip().lower())
    h = hashlib.md5(query.encode()).hexdigest()[:8]
    return f"{q[:40]}_{h}"


# ── 씬 타입 추론 (utils.ts inferSceneType 포팅) ─────────────────────────────

_SOL_WORDS = ["방법이 있", "방법은", "하세요", "해보세요", "하면 됩니다", "루틴", "습관을",
              "바꾸", "개선", "극복", "늘리", "줄이", "비결", "실천", "멈추세요",
              "차단", "저널링", "명상", "시작하세요"]
_STAT_WORDS = ["통계", "연구에 따르면", "연구 결과", "조사에 따르면", "데이터", "수치",
               "기록에 따르면", "역사 기록", "이 수치", "이 통계", "퍼센트가", "명 중"]


def _infer_scene_type(index: int, total: int, narration: str) -> str:
    """씬 위치와 나레이션으로 타입 추론 (utils.ts와 동일 로직)."""
    if index == 1:
        return "hook"
    if index >= total - 1:
        return "closing"
    if '"' in narration or '\u201c' in narration or '\u201d' in narration:
        return "quote"
    if any(w in narration for w in _SOL_WORDS):
        return "solution"
    if re.search(r"(?:첫 번째|두 번째|세 번째|네 번째|다섯 번째|\d+\.\s|\d+번째)", narration):
        return "numbered"
    if any(w in narration for w in _STAT_WORDS):
        return "stat"
    if index == 2 and re.search(r"\d+[%배만억초분시간일년]", narration):
        return "hook_data"
    return "problem"


# ── 씬 타입별 이미지 스타일 가이드 ────────────────────────────────────────────
# 피사체 없는 순수 카메라/조명 지시 → 구체적 피사체 묘사 + 조명 + 분위기 통합
_SCENE_TYPE_STYLE: dict[str, str] = {
    # 역사원정대/역사노트급 시네마틱: 극도의 명암, 영화 조명, 실사 렌더링
    "hook":      "extreme close-up, single harsh key light cutting through absolute darkness, rim light outlining subject edge, razor-sharp cinematic focus, IMAX film quality, anamorphic lens flare",
    "hook_data": "low-angle hero shot, dramatic shaft of light from above, deep shadows on 80% of frame, bold isolated subject, epic cinematic composition, film grain",
    "problem":   "wide oppressive shot, cold desaturated steel-blue, ominous overcast atmosphere, subject small in vast threatening environment, deep chiaroscuro, heavy shadows, tense cinematic",
    "numbered":  "dramatic side-lit 45 degrees, bold single symbolic subject against dark gradient void, crisp hyperreal texture detail, cinematic tableau composition",
    "solution":  "backlit golden hour, subject emerging from shadow into warm amber-gold radiant light, volumetric light rays, hopeful cinematic atmosphere, shallow depth of field bokeh",
    "stat":      "macro abstract, bioluminescent particles or light threads on jet black, ethereal scientific atmosphere, no numbers or text visible, cinematic micro photography",
    "quote":     "intimate rembrandt portrait lighting, single soft key light on face or symbolic object, 80% shadow coverage, contemplative philosophical mood, film still quality",
    "closing":   "ultra wide anamorphic panorama, lone silhouette against vast luminous sky, epic scale, golden or violet atmospheric haze, emotional cinematic finale, God rays",
}

_IMAGE_STYLE_SUFFIX: dict[int, str] = {
    0: "",
    1: "photorealistic cinematic still, realistic texture detail",
    2: "watercolor painting style, soft brush strokes, paper texture",
    3: "cartoon illustration style, bold outlines, clean cel shading",
    4: "anime style illustration, dynamic composition, vibrant cel-shaded lighting",
    5: "oil painting style, rich impasto texture, classical brushwork",
    6: "pencil sketch style, graphite shading, monochrome line art",
    7: "minimal white-face character style, simple geometric face, expressive body language",
}


# ── Gemini 이미지 생성 (google-genai SDK) ─────────────────────────────────────

def _extract_visual_concept(narration: str, max_len: int = 150) -> str:
    """[미사용] 나레이션에서 핵심 시각적 개념 추출.

    _build_prompt가 narration_hint 방식을 제거했으므로 호출되지 않음.
    한국어를 Gemini 프롬프트에 삽입하면 이미지 품질이 저하됨.
    Claude 템플릿이 image_prompt에 이미 나레이션 개념을 영문으로 반영함.
    """
    if not narration:
        return ""
    cleaned = re.sub(r"(여러분|사실|그런데|하지만|즉|결국|바로|그래서|왜냐하면)\s*", "", narration)
    if "—" in cleaned or " - " in cleaned:
        parts = re.split(r"[—]|\s-\s", cleaned, maxsplit=1)
        if len(parts) > 1 and len(parts[1].strip()) > 10:
            cleaned = parts[1].strip()
    if len(cleaned) > max_len:
        m = re.search(r"^(.{20,}?)[。.!?！？]", cleaned)
        if m:
            cleaned = m.group(1)
        else:
            cleaned = cleaned[:max_len]
    return cleaned.strip()


def _build_prompt(scene_prompt: str, context: dict) -> str:
    """3단계 프롬프트 엔지니어링 전략.

    구조: [씬 핵심 묘사] + [씬타입 시각 스타일] + [카테고리 분위기 suffix]

    변경 이유:
    - prefix 제거: "[YouTube Shorts series...]" 메타텍스트가 이미지 글자 오염 유발
    - narration_hint 제거: Claude가 이미 image_prompt에 반영했으므로 한국어 중복 삽입 금지
    - scene_prompt가 핵심 — Claude 템플릿이 생성한 영문 묘사를 최대한 살림
    """
    category = context.get("category", "")
    scene_type = context.get("scene_type", "problem")

    # ── 1단계: 씬 핵심 묘사 (Claude 생성 image_prompt) ──────────────
    core = scene_prompt.strip()

    # ── 2단계: 씬 타입별 시각 스타일 (카메라 + 조명 + 분위기) ──────────────
    type_style = _SCENE_TYPE_STYLE.get(scene_type, "dramatic cinematic lighting, dark atmosphere")

    # ── 3단계: 카테고리별 색감/분위기 suffix ──────────────────────────
    suffix = _CATEGORY_SUFFIX.get(
        category,
        "dramatic cinematic, hyper-realistic rendering, no text, no letters, no watermark, no UI elements"
    )

    style_suffix = _IMAGE_STYLE_SUFFIX.get(int(context.get("image_style", 0) or 0), "")
    if style_suffix:
        return f"{core}, {type_style}, {suffix}, {style_suffix}"
    return f"{core}, {type_style}, {suffix}"


def _generate_gemini(prompt: str, api_key: str, context: dict | None = None) -> str | None:
    """google-genai SDK로 이미지 생성. 캐시 경로 반환, 실패 시 None.

    429 쿼터 소진 시 즉시 None 반환 (재시도 없음).
    """
    global _gemini_quota_exhausted
    if _gemini_quota_exhausted:
        return None

    _GEMINI_CACHE.mkdir(parents=True, exist_ok=True)

    # 컨텍스트 포함한 전체 프롬프트로 캐시 키 생성
    full_prompt = _build_prompt(prompt, context or {})
    h = hashlib.md5(full_prompt.encode()).hexdigest()[:12]
    cache_path = _GEMINI_CACHE / f"{h}.png"

    if cache_path.exists() and cache_path.stat().st_size > 1000:
        return str(cache_path)

    # 모델명 고정 — 사용자 지정값 우선, 기본값은 gemini-3.1-flash-image-preview
    model_name = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

    for retry_wait in [0, 5, 15, 30]:  # 429 발생 시 단계적 대기 (초)
        if retry_wait > 0:
            print(f"      Gemini rate limit — {retry_wait}초 대기 후 재시도")
            time.sleep(retry_wait)
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(aspect_ratio="9:16"),
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    cache_path.write_bytes(part.inline_data.data)
                    return str(cache_path)

            print(f"      Gemini: 이미지 없음 (텍스트만 반환)")
            return None

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if retry_wait == 30:
                    # 최대 재시도 소진 → 이번 씬만 건너뜀 (전체 중단 안 함)
                    print(f"      Gemini 429 — 재시도 소진, 이번 씬 스킵")
                    return None
                # 다음 루프에서 대기 후 재시도
                continue
            elif "QUOTA_EXCEEDED" in err_str or "quota" in err_str.lower():
                print(f"      Gemini 일일 쿼터 소진 — 이미지 생성 중단")
                _gemini_quota_exhausted = True
                return None
            else:
                print(f"      Gemini 예외: {e}")
                return None

    return None


def reset_gemini_quota_flag() -> None:
    """테스트 또는 재시도 시 쿼터 플래그 초기화."""
    global _gemini_quota_exhausted
    _gemini_quota_exhausted = False


# ── Pexels / Pixabay ──────────────────────────────────────────────────────────

def _fetch_pexels(query: str, api_key: str) -> str | None:
    url = f"{_PEXELS_API}?query={urllib.parse.quote(query)}&per_page=5&orientation=portrait"
    req = urllib.request.Request(url, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            photos = data.get("photos", [])
            if photos:
                return photos[0]["src"]["large"]
    except Exception:
        pass
    return None


def _fetch_pixabay(query: str, api_key: str) -> str | None:
    url = (
        f"{_PIXABAY_API}?key={api_key}"
        f"&q={urllib.parse.quote(query)}"
        f"&image_type=photo&orientation=vertical&per_page=5"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            hits = data.get("hits", [])
            if hits:
                return hits[0].get("largeImageURL") or hits[0].get("webformatURL")
    except Exception:
        pass
    return None


def _download(img_url: str, cache_path: Path) -> str | None:
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) > 1000:
            cache_path.write_bytes(data)
            return str(cache_path)
    except Exception:
        pass
    return None


# ── 공개 API ──────────────────────────────────────────────────────────────────

def _stock_search_query(image_prompt: str, context: dict) -> str:
    """Pexels/Pixabay용 짧은 검색 키워드 추출.

    image_prompt 전체(100자+)를 그대로 검색하면 결과 없음.
    첫 10단어 또는 쉼표 전 첫 구절만 사용.
    """
    scene_type = context.get("scene_type", "")
    category = context.get("category", "")

    # 씬타입 + 카테고리 기반 폴백 키워드 (검색 최적화)
    _FALLBACK_QUERIES: dict[str, dict[str, str]] = {
        "심리학": {
            "hook": "human brain psychology dark",
            "problem": "anxiety stress dark cinematic",
            "numbered": "mind psychology concept",
            "solution": "freedom light hope",
            "stat": "data abstract dark",
            "closing": "cosmos silhouette night",
            "hook_data": "brain neuron glow",
            "quote": "contemplation solitude",
        },
        "역사 충격": {
            "hook": "ancient history dramatic",
            "problem": "dark historical mystery",
            "numbered": "history artifact dramatic",
            "solution": "heritage enlightenment",
            "stat": "historical data ancient",
            "closing": "epic historical landscape",
            "hook_data": "ancient document scroll",
            "quote": "historical figure portrait",
        },
        "뇌과학": {
            "hook": "neuroscience brain glow",
            "problem": "brain fatigue stress science",
            "numbered": "neural network science",
            "solution": "brain clarity focus light",
            "stat": "neuroscience data abstract",
            "closing": "mind cosmos silhouette",
            "hook_data": "brain scan neural",
            "quote": "scientist contemplation",
        },
        "한국사 X파일": {
            "hook": "ancient Korean history dramatic",
            "problem": "dark Korean history mystery",
            "numbered": "Korean heritage artifact",
            "solution": "Korean tradition wisdom",
            "stat": "historical Korean data",
            "closing": "Korean landscape epic",
            "hook_data": "ancient Korean document",
            "quote": "Korean historical figure",
        },
        "돈의 심리학": {
            "hook": "wealth money psychology dark",
            "problem": "financial stress dark cinematic",
            "numbered": "investment strategy abstract",
            "solution": "wealth growth success light",
            "stat": "financial data chart dark",
            "closing": "success achievement horizon",
            "hook_data": "gold wealth abstract",
            "quote": "business wisdom portrait",
        },
    }

    fallback = _FALLBACK_QUERIES.get(category, {}).get(scene_type, "")
    if fallback:
        return fallback

    # 폴백 없으면 image_prompt 첫 쉼표 전 구절 (최대 40자)
    first_clause = image_prompt.split(",")[0].strip()
    return first_clause[:40] if first_clause else "cinematic dark dramatic"


def fetch_bg_image(query: str, context: dict | None = None) -> str | None:
    """씬 프롬프트로 배경 이미지 경로 반환.

    우선순위: Gemini → Pexels → Pixabay
    실패 시 None.
    """
    if not query or not query.strip():
        return None

    ctx = context or {}
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "")

    # 1. Gemini 이미지 생성
    if gemini_key and not _gemini_quota_exhausted:
        path = _generate_gemini(query, gemini_key, ctx)
        if path:
            return path

    # Pexels/Pixabay용 짧은 검색 키워드 (image_prompt 전체 금지)
    stock_query = _stock_search_query(query, ctx)

    # 2. Pexels
    if pexels_key:
        _STOCK_CACHE.mkdir(parents=True, exist_ok=True)
        cache_path = _STOCK_CACHE / f"{_sanitize(stock_query)}.jpg"
        if cache_path.exists() and cache_path.stat().st_size > 1000:
            return str(cache_path)
        img_url = _fetch_pexels(stock_query, pexels_key)
        if img_url:
            return _download(img_url, cache_path)

    # 3. Pixabay
    if pixabay_key:
        _STOCK_CACHE.mkdir(parents=True, exist_ok=True)
        cache_path = _STOCK_CACHE / f"{_sanitize(stock_query)}.jpg"
        if cache_path.exists() and cache_path.stat().st_size > 1000:
            return str(cache_path)
        img_url = _fetch_pixabay(stock_query, pixabay_key)
        if img_url:
            return _download(img_url, cache_path)

    return None


# ── 카테고리별 Gemini 스타일 가이드 ──────────────────────────────────────────
# 3단계 전략: 공통 스타일 suffix — 모든 씬에 동일하게 적용해 시각적 일관성 확보

_CATEGORY_STYLE: dict[str, str] = {
    "심리학":       "deep purple dark navy, violet neural glow, psychological dark cinematic",
    "역사 충격":    "dark crimson burnt amber, torchlight, ancient dramatic cinematic",
    "뇌과학":       "electric blue teal glow, neural network, dark scientific cinematic",
    "한국사 X파일": "dark crimson gold accent, ancient Korean aesthetic, cinematic",
    "돈의 심리학":  "deep forest green gold accent, dark financial premium cinematic",
}

# 카테고리별 고화질 공통 스타일 suffix (모든 씬 프롬프트 뒤에 붙임)
# 시각적 일관성 + 고품질 렌더링 지시
_CATEGORY_SUFFIX: dict[str, str] = {
    # 역사원정대/역사노트 수준의 시네마틱 이미지 품질
    # 카테고리 색감 고정 + 영화급 렌더링 품질 지시
    "심리학":       "deep purple indigo violet color grade, psychological noir cinematic, photorealistic 8K render, professional cinematography, no text no letters no watermark no UI no subtitles",
    "역사 충격":    "dark crimson amber torchlight color grade, ancient world cinematic epic, photorealistic 8K render, professional cinematography, no text no letters no watermark no UI no subtitles",
    "뇌과학":       "electric blue cyan teal color grade, biopunk scientific cinematic, photorealistic 8K render, professional cinematography, no text no letters no watermark no UI no subtitles",
    "한국사 X파일": "dark ink black gold crimson color grade, Joseon dynasty cinematic epic, photorealistic 8K render, professional cinematography, no text no letters no watermark no UI no subtitles",
    "돈의 심리학":  "deep emerald black gold color grade, premium financial noir cinematic, photorealistic 8K render, professional cinematography, no text no letters no watermark no UI no subtitles",
}


def fetch_bg_images_for_script(
    scenes: list[dict],
    delay: float = 1.0,
    title: str = "",
    category: str = "",
    image_style: int = 0,
) -> dict[int, str]:
    """스크립트 씬 전체 배경 이미지 조달.

    Args:
        scenes: [{"index": 1, "image_prompt": "...", "video_query": "..."}, ...]
        delay: 씬 간 호출 간격 (초) — Gemini rate limit 방지
        title: 영상 제목 (시리즈 컨텍스트 prefix용)
        category: 카테고리명 (스타일 가이드 자동 선택)

    Returns:
        {scene_index: image_path}
    """
    reset_gemini_quota_flag()
    total = len(scenes)
    # 시리즈 컨텍스트용 스타일 (prefix에 삽입) — suffix는 _build_prompt 내부에서 자동 적용
    style = _CATEGORY_STYLE.get(category, "dark cinematic dramatic")

    result: dict[int, str] = {}
    for scene in scenes:
        idx = scene.get("index", 0)
        query = (
            scene.get("image_prompt")
            or scene.get("imagePrompt")
            or scene.get("video_query")
            or ""
        )
        if not query:
            continue

        narration = scene.get("narration", "")
        scene_type = _infer_scene_type(idx, total, narration)

        context = {
            "title": title,
            "category": category,
            "style": style,
            "image_style": image_style,
            "scene_index": idx,
            "total_scenes": total,
            "narration": narration,
            "scene_type": scene_type,
        }

        path = fetch_bg_image(query, context)
        if path:
            result[idx] = path

        if delay > 0:
            time.sleep(delay)

    return result
