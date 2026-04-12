"""YouTube 쇼츠/롱폼 자동화 파이프라인 설정."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

# --- 프로젝트 경로 ---
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# --- Claude API ---
MODEL_NAME = "claude-sonnet-4-5-20250514"
USE_CLAUDE_API = os.environ.get("USE_CLAUDE_API", "").strip().lower() in {"1", "true", "yes", "on"}

# --- 카테고리 설정 ---
CATEGORIES = [
    {
        "id": 1,
        "name": "심리학",
        "desc": "일상 속 심리 현상, 행동경제학, 인간관계",
        "emoji": "\U0001f9e0",
        "voice": "ko-KR-SunHiNeural",
        "shorts_rate": "+15%",
        "longform_rate": "+5%",
        "pitch": "+0Hz",
        "search_query": "심리학 유튜브 쇼츠 트렌드 최신",
        # 벤치마킹 분석 기반 포맷 설정
        # 패턴: 숫자 통계 훅 → 심리 편향 problem × 3 → solution → closing
        # 핵심: subtitle에 숫자+단위 포함 (카운트업 애니메이션 트리거)
        # 예: "73%가 모른다", "2배 더 강하다", "47초밖에 안 된다"
        "script_template": "shorts_script_psychology.txt",
        "scene_format": {
            "total_scenes": 8,
            "duration_seconds": 58,
            "structure": [
                {"role": "hook",     "duration": 3,  "hint": "충격 통계 수치로 시작. subtitle에 숫자+단위 필수 (예: 73%, 2배, 3초)"},
                {"role": "problem",  "duration": 8,  "hint": "이 현상이 왜 일어나는지 문제 제기. 나레이션에 심리학 용어 포함"},
                {"role": "numbered", "duration": 8,  "hint": "첫 번째 이유: 구체적 심리 메커니즘 설명"},
                {"role": "numbered", "duration": 8,  "hint": "두 번째 이유: 행동경제학적 근거 또는 실험 결과"},
                {"role": "numbered", "duration": 8,  "hint": "세 번째 이유: 일상 속 사례로 연결"},
                {"role": "solution", "duration": 8,  "hint": "이 심리를 역이용하는 실용적 방법 제시"},
                {"role": "closing",  "duration": 8,  "hint": "핵심 메시지 한 문장 + 반전 또는 여운"},
                {"role": "closing",  "duration": 7,  "hint": "구독/좋아요 CTA. subtitle: '구독 클릭'"},
            ],
        },
        "longform_script_template": "longform_script_psychology.txt",
        "longform_scene_format": {
            "total_scenes": 14,
            "duration_seconds": 540,
            "structure": [
                {"role": "hook",     "duration": 15, "hint": "충격 통계 수치로 시작. subtitle에 숫자 필수"},
                {"role": "hook",     "duration": 15, "hint": "핵심 수치만 크게 강조하는 씬"},
                {"role": "problem",  "duration": 30, "hint": "심리학적 배경 설명. 심리 용어 포함"},
                {"role": "numbered", "duration": 45, "hint": "첫 번째 이유: 핵심 심리 메커니즘 + 연구 결과"},
                {"role": "numbered", "duration": 30, "hint": "관련 통계/실험 수치 강조 씬"},
                {"role": "numbered", "duration": 45, "hint": "두 번째 이유: 행동경제학적 근거 + 사례"},
                {"role": "numbered", "duration": 45, "hint": "세 번째 이유: 일상 속 사례로 연결"},
                {"role": "quote",    "duration": 30, "hint": "심리학자 또는 철학자 실제 명언. 큰따옴표 필수"},
                {"role": "solution", "duration": 45, "hint": "첫 번째 방법: 즉시 실천 가능한 구체적 팁"},
                {"role": "solution", "duration": 45, "hint": "두 번째 방법: 과학적 근거 있는 루틴"},
                {"role": "solution", "duration": 45, "hint": "세 번째 방법: 장기 습관으로 연결"},
                {"role": "stat",     "duration": 30, "hint": "방법 적용 시 기대 효과 수치. subtitle에 숫자 필수"},
                {"role": "closing",  "duration": 30, "hint": "핵심 메시지 한 문장 + 감성적 마무리"},
                {"role": "closing",  "duration": 30, "hint": "구독/좋아요 CTA + 다음 영상 예고"},
            ],
        },
    },
    {
        "id": 2,
        "name": "역사 충격",
        "desc": "교과서에 없는 역사 뒷이야기, 미스터리",
        "emoji": "\U0001f4dc",
        "voice": "ko-KR-InJoonNeural",
        "shorts_rate": "+10%",
        "longform_rate": "+0%",
        "pitch": "-5Hz",
        "search_query": "역사 미스터리 유튜브 인기 최신",
        # 벤치마킹 분석 기반 포맷 설정
        # 패턴: 충격 수치 훅 → 통념 반박 problem → 역사 사실 numbered × 3 → 반전 closing
        # 핵심: subtitle에 구체적 수치 (생존율 90%, 합격률 0.3%, 170cm 등)
        # 인용구가 있으면 quote 씬 적극 활용
        "script_template": "shorts_script_history.txt",
        "scene_format": {
            "total_scenes": 8,
            "duration_seconds": 58,
            "structure": [
                {"role": "hook",     "duration": 4,  "hint": "교과서와 다른 충격 수치로 시작. subtitle에 구체적 숫자 필수 (예: 90% 생존, 0.3% 합격)"},
                {"role": "problem",  "duration": 7,  "hint": "우리가 알던 상식이 틀렸다는 것을 제시. '영화/교과서가 거짓말을 했다' 식으로"},
                {"role": "numbered", "duration": 8,  "hint": "첫 번째 충격 사실: 구체적 역사 근거와 수치"},
                {"role": "numbered", "duration": 8,  "hint": "두 번째 충격 사실: 더 놀라운 숨겨진 배경"},
                {"role": "numbered", "duration": 8,  "hint": "세 번째 충격 사실: 현재와의 연결 또는 최대 반전"},
                {"role": "quote",    "duration": 7,  "hint": "당시 역사적 인물의 실제 발언 인용 또는 역사 기록 인용. 큰따옴표 필수"},
                {"role": "closing",  "duration": 9,  "hint": "역사에서 배울 수 있는 교훈 한 문장 + 다음 영상 예고"},
                {"role": "closing",  "duration": 7,  "hint": "구독/좋아요 CTA"},
            ],
        },
        "longform_script_template": "longform_script_history.txt",
        "longform_scene_format": {
            "total_scenes": 14,
            "duration_seconds": 540,
            "structure": [
                {"role": "hook",     "duration": 15, "hint": "교과서와 다른 충격 수치. subtitle에 숫자 필수"},
                {"role": "hook",     "duration": 15, "hint": "핵심 수치만 크게 강조. subtitle이 메인 비주얼"},
                {"role": "problem",  "duration": 30, "hint": "우리가 잘못 알고 있는 통념 지적"},
                {"role": "numbered", "duration": 45, "hint": "첫 번째 충격 사실: 구체적 역사 근거 + 수치"},
                {"role": "stat",     "duration": 30, "hint": "관련 역사 통계/수치 강조. subtitle에 숫자 필수"},
                {"role": "numbered", "duration": 45, "hint": "두 번째 충격 사실: 더 놀라운 숨겨진 배경"},
                {"role": "numbered", "duration": 45, "hint": "세 번째 충격 사실: 최대 반전 또는 현재와의 연결"},
                {"role": "quote",    "duration": 30, "hint": "역사적 인물의 실제 발언. 큰따옴표 필수"},
                {"role": "numbered", "duration": 45, "hint": "네 번째 충격 사실: 후속 사건 또는 결과"},
                {"role": "numbered", "duration": 45, "hint": "다섯 번째 충격 사실: 현대와의 연결고리"},
                {"role": "stat",     "duration": 30, "hint": "역사적 영향 수치 강조. subtitle에 숫자 필수"},
                {"role": "quote",    "duration": 30, "hint": "역사가 또는 목격자 증언. 큰따옴표 필수"},
                {"role": "closing",  "duration": 30, "hint": "역사에서 배울 교훈 + 감성적 마무리"},
                {"role": "closing",  "duration": 30, "hint": "구독/좋아요 CTA + 다음 역사 영상 예고"},
            ],
        },
    },
    {
        "id": 3,
        "name": "뇌과학",
        "desc": "수면, 집중력, 도파민, 뇌 최적화",
        "emoji": "\U0001f52c",
        "voice": "ko-KR-SunHiNeural",
        "shorts_rate": "+15%",
        "longform_rate": "+5%",
        "pitch": "+0Hz",
        "search_query": "뇌과학 자기계발 유튜브 트렌드 최신",
        # 벤치마킹 분석 기반 포맷 설정
        # 패턴: 수치 훅 → 과학적 메커니즘 problem → numbered 방법 × 3~5 → solution 루틴
        # 핵심: 연구 결과 수치 (40% 저하, 47초, 8시간) + 실용적 solution 씬
        # '이렇게 하면 된다' solution 씬이 핵심 — 조회수 유지율 최고 구간
        "script_template": "shorts_script_brain.txt",
        "scene_format": {
            "total_scenes": 9,
            "duration_seconds": 58,
            "structure": [
                {"role": "hook",     "duration": 3,  "hint": "뇌과학 연구 수치로 충격 훅. subtitle에 숫자 필수 (예: 47초, 40% 저하, 2배 향상)"},
                {"role": "problem",  "duration": 7,  "hint": "현대인이 겪는 문제와 뇌과학적 원인 연결. 도파민/코르티솔/전두엽 등 키워드 사용"},
                {"role": "numbered", "duration": 7,  "hint": "첫 번째 뇌과학 근거: 연구 결과나 실험으로 증명된 사실"},
                {"role": "numbered", "duration": 7,  "hint": "두 번째 뇌과학 근거: 뇌의 구체적 메커니즘 설명"},
                {"role": "numbered", "duration": 7,  "hint": "세 번째 뇌과학 근거: 나쁜 습관이 뇌에 미치는 영향"},
                {"role": "solution", "duration": 8,  "hint": "첫 번째 해결책: 즉시 실천 가능한 구체적 방법. '하루 X분' 또는 'X일이면' 수치 포함"},
                {"role": "solution", "duration": 8,  "hint": "두 번째 해결책: 과학적 근거가 있는 루틴 또는 습관"},
                {"role": "closing",  "duration": 4,  "hint": "뇌과학이 증명한 핵심 메시지 한 문장"},
                {"role": "closing",  "duration": 7,  "hint": "구독/좋아요 CTA"},
            ],
        },
        "longform_script_template": "longform_script_brain.txt",
        "longform_scene_format": {
            "total_scenes": 15,
            "duration_seconds": 540,
            "structure": [
                {"role": "hook",     "duration": 15, "hint": "뇌과학 연구 충격 수치. subtitle에 숫자 필수"},
                {"role": "hook",     "duration": 15, "hint": "수치 강조 씬. 현대인이 겪는 문제 직관적 표현"},
                {"role": "problem",  "duration": 30, "hint": "뇌과학적 원인. 도파민/전두엽/코르티솔 키워드"},
                {"role": "stat",     "duration": 30, "hint": "연구 결과 수치 강조. subtitle에 숫자 필수"},
                {"role": "numbered", "duration": 45, "hint": "첫 번째 근거: 연구/실험으로 증명된 사실"},
                {"role": "numbered", "duration": 45, "hint": "두 번째 근거: 뇌 메커니즘 상세 설명"},
                {"role": "stat",     "duration": 30, "hint": "나쁜 습관이 뇌에 미치는 영향 수치"},
                {"role": "numbered", "duration": 45, "hint": "세 번째 근거: 일상 습관과 뇌의 연결"},
                {"role": "quote",    "duration": 30, "hint": "뇌과학자 또는 신경과학 연구 인용. 큰따옴표 필수"},
                {"role": "solution", "duration": 45, "hint": "첫 번째 방법: 즉시 실천 가능. '하루 X분이면' 수치 포함"},
                {"role": "solution", "duration": 45, "hint": "두 번째 방법: 수면/식단/운동 뇌과학 근거"},
                {"role": "solution", "duration": 45, "hint": "세 번째 방법: 장기 루틴으로 뇌 구조 변화"},
                {"role": "stat",     "duration": 30, "hint": "방법 적용 후 뇌 변화 수치. subtitle에 숫자 필수"},
                {"role": "closing",  "duration": 30, "hint": "핵심 메시지 + 뇌과학이 증명한 결론"},
                {"role": "closing",  "duration": 30, "hint": "구독/좋아요 CTA + 다음 영상 예고"},
            ],
        },
    },
    {
        "id": 4,
        "name": "한국사 X파일",
        "desc": "조선, 일제강점기 숨겨진 이야기",
        "emoji": "\U0001f3ef",
        "voice": "ko-KR-HyunsuNeural",
        "shorts_rate": "+10%",
        "longform_rate": "+0%",
        "pitch": "+0Hz",
        "search_query": "한국사 충격 비화 유튜브 인기 최신",
        # 벤치마킹 분석 기반 포맷 설정
        # 패턴: 충격 수치 훅 → 역사 배경 problem → 숨겨진 사실 numbered × 3 → 실제 기록 quote → 교훈 closing
        # 핵심: 구체적 수치 (0.3% 합격, 13첩 반상, 13년 투쟁 등) + 역사 기록 인용 quote
        # 감성적 closing이 공유율 높음 — 민족 자긍심 또는 안타까움 자극
        "script_template": "shorts_script_korean_history.txt",
        "scene_format": {
            "total_scenes": 8,
            "duration_seconds": 58,
            "structure": [
                {"role": "hook",     "duration": 4,  "hint": "한국사 속 충격 수치 또는 '교과서에 없는' 사실로 시작. subtitle에 숫자 필수"},
                {"role": "problem",  "duration": 7,  "hint": "우리가 몰랐던 이유 — 역사가 지워진 배경 제시. 일제 식민사관 또는 왜곡된 역사 언급 가능"},
                {"role": "numbered", "duration": 8,  "hint": "첫 번째 숨겨진 사실: 구체적 역사 기록과 수치로 뒷받침"},
                {"role": "numbered", "duration": 8,  "hint": "두 번째 숨겨진 사실: 더 충격적인 사실 또는 인물 이야기"},
                {"role": "numbered", "duration": 8,  "hint": "세 번째 숨겨진 사실: 현재와 연결되는 의미 있는 사실"},
                {"role": "quote",    "duration": 7,  "hint": "실제 역사 인물의 발언이나 기록 인용. 큰따옴표 필수. 안중근/세종/유관순 등"},
                {"role": "closing",  "duration": 7,  "hint": "역사에서 얻는 교훈 + 민족적 자긍심 또는 반성 메시지"},
                {"role": "closing",  "duration": 7,  "hint": "구독/좋아요 CTA"},
            ],
        },
        "longform_script_template": "longform_script_korean_history.txt",
        "longform_scene_format": {
            "total_scenes": 14,
            "duration_seconds": 540,
            "structure": [
                {"role": "hook",     "duration": 15, "hint": "한국사 충격 수치 또는 '교과서에 없는' 사실. subtitle에 숫자 필수"},
                {"role": "hook",     "duration": 15, "hint": "핵심 수치 강조 씬"},
                {"role": "problem",  "duration": 30, "hint": "우리가 몰랐던 이유. 역사 왜곡 또는 숨겨진 배경"},
                {"role": "numbered", "duration": 45, "hint": "첫 번째 숨겨진 사실: 역사 기록과 수치"},
                {"role": "stat",     "duration": 30, "hint": "관련 역사 통계 강조. subtitle에 숫자 필수"},
                {"role": "numbered", "duration": 45, "hint": "두 번째 숨겨진 사실: 더 충격적인 사실"},
                {"role": "numbered", "duration": 45, "hint": "세 번째 숨겨진 사실: 현재와 연결"},
                {"role": "quote",    "duration": 30, "hint": "역사 인물 실제 발언 또는 기록. 큰따옴표 필수"},
                {"role": "numbered", "duration": 45, "hint": "네 번째 숨겨진 사실: 국제적 맥락"},
                {"role": "numbered", "duration": 45, "hint": "다섯 번째 숨겨진 사실: 최대 반전"},
                {"role": "stat",     "duration": 30, "hint": "역사적 영향력 수치. subtitle에 숫자 필수"},
                {"role": "quote",    "duration": 30, "hint": "역사가 또는 독립운동가 발언. 큰따옴표 필수"},
                {"role": "closing",  "duration": 30, "hint": "역사 교훈 + 민족 자긍심 감성 마무리"},
                {"role": "closing",  "duration": 30, "hint": "구독/좋아요 CTA + 다음 한국사 영상 예고"},
            ],
        },
    },
    {
        "id": 5,
        "name": "돈의 심리학",
        "desc": "부자 습관, 행동경제학, 투자 심리",
        "emoji": "\U0001f4b0",
        "voice": "ko-KR-InJoonNeural",
        "shorts_rate": "+10%",
        "longform_rate": "+0%",
        "pitch": "+0Hz",
        "search_query": "재테크 부자 심리 유튜브 트렌드 최신",
        # 벤치마킹 분석 기반 포맷 설정
        # 패턴: 돈 관련 충격 수치 훅 → 심리 편향 problem → 부자 습관 numbered × 3 → 워런버핏 등 명언 quote → 실천법 solution
        # 핵심: 복리/손실/수익 수치 카운트업 + 유명 투자자 명언 quote 씬
        # '지금 당장 할 수 있는' solution이 저장/공유율 최고
        "script_template": "shorts_script_money.txt",
        "scene_format": {
            "total_scenes": 8,
            "duration_seconds": 58,
            "structure": [
                {"role": "hook",     "duration": 4,  "hint": "돈과 관련된 충격 수치로 시작. subtitle에 금액/퍼센트/배수 필수 (예: 2배, 20%, 100만원)"},
                {"role": "problem",  "duration": 7,  "hint": "대부분의 사람이 이 심리 편향 때문에 가난해지는 이유. 손실회피/앵커링/매몰비용 등 용어 사용"},
                {"role": "numbered", "duration": 8,  "hint": "첫 번째 부자의 비밀: 구체적 습관이나 심리 전략 + 수치 근거"},
                {"role": "numbered", "duration": 8,  "hint": "두 번째 부자의 비밀: 행동경제학 연구 결과 또는 투자 원칙"},
                {"role": "numbered", "duration": 8,  "hint": "세 번째 부자의 비밀: 지금 당장 적용 가능한 실천 방법"},
                {"role": "quote",    "duration": 6,  "hint": "워런 버핏, 찰리 멍거, 레이 달리오 등 유명 투자자 실제 명언. 큰따옴표 필수"},
                {"role": "solution", "duration": 8,  "hint": "오늘부터 할 수 있는 구체적 실천법. '매달 X만원', 'X년이면' 등 수치로 동기부여"},
                {"role": "closing",  "duration": 7,  "hint": "구독/좋아요 CTA + 다음 영상 예고"},
            ],
        },
        "longform_script_template": "longform_script_money.txt",
        "longform_scene_format": {
            "total_scenes": 14,
            "duration_seconds": 540,
            "structure": [
                {"role": "hook",     "duration": 15, "hint": "돈 관련 충격 수치. subtitle에 금액/퍼센트 필수"},
                {"role": "hook",     "duration": 15, "hint": "핵심 수치 강조. 'X%만 알면 인생이 바뀐다' 톤"},
                {"role": "problem",  "duration": 30, "hint": "심리 편향 때문에 가난해지는 이유"},
                {"role": "stat",     "duration": 30, "hint": "빈부격차 또는 금융 관련 충격 통계"},
                {"role": "numbered", "duration": 45, "hint": "첫 번째 비밀: 부자들의 구체적 심리 전략 + 수치"},
                {"role": "numbered", "duration": 45, "hint": "두 번째 비밀: 행동경제학 연구 결과"},
                {"role": "quote",    "duration": 30, "hint": "워런 버핏/찰리 멍거 등 실제 명언. 큰따옴표 필수"},
                {"role": "numbered", "duration": 45, "hint": "세 번째 비밀: 복리/투자 원칙 수치로 설명"},
                {"role": "numbered", "duration": 45, "hint": "네 번째 비밀: 지금 당장 적용 가능한 전략"},
                {"role": "stat",     "duration": 30, "hint": "전략 적용 시 기대 수익 수치. subtitle에 숫자 필수"},
                {"role": "solution", "duration": 45, "hint": "오늘부터 시작하는 방법: 구체적 실천법 + 수치"},
                {"role": "quote",    "duration": 30, "hint": "두 번째 투자 거장 명언. 큰따옴표 필수"},
                {"role": "closing",  "duration": 30, "hint": "핵심 메시지 + 동기부여 마무리"},
                {"role": "closing",  "duration": 30, "hint": "구독/좋아요 CTA + 다음 영상 예고"},
            ],
        },
    },
    {
        "id": 6,
        "name": "경제 다큐",
        "desc": "금리, 환율, 부동산, 글로벌 경제 위기",
        "emoji": "\U0001f4ca",
        "voice": "ko-KR-InJoonNeural",
        "shorts_rate": "+10%",
        "longform_rate": "+0%",
        "pitch": "-5Hz",
        "search_query": "경제 위기 다큐 유튜브 인기 최신",
        # 벤치마킹 분석 기반 포맷 설정
        # 패턴: 충격 경제 수치 훅 → 구조적 원인 problem → 데이터 기반 numbered × 3 → 전문가 인용 quote → 대응 전략 solution
        # 핵심: 경제 지표 수치 카운트업 (GDP%, 금리%, 부채비율) + 역사적 사례 비교
        # '지금 당장 할 수 있는 전략' solution이 저장/공유율 최고
        "script_template": "shorts_script_economy.txt",
        "scene_format": {
            "total_scenes": 10,
            "duration_seconds": 88,
            "structure": [
                {"role": "hook",     "duration": 4,  "hint": "경제 충격 수치로 시작. subtitle에 숫자+단위 필수 (예: GDP 3% 붕괴, 10년 만에 2배, 1조 증발)"},
                {"role": "problem",  "duration": 9,  "hint": "이 경제 현상의 구조적 원인 설명. 금리/인플레이션/유동성 등 전문 용어 포함"},
                {"role": "numbered", "duration": 11, "hint": "첫 번째 팩트: 데이터/통계 기반 핵심 경제 사실"},
                {"role": "numbered", "duration": 11, "hint": "두 번째 팩트: 글로벌 또는 역사적 사례와 비교"},
                {"role": "numbered", "duration": 11, "hint": "세 번째 팩트: 현재 한국/세계 경제와의 연결"},
                {"role": "stat",     "duration": 7,  "hint": "핵심 경제 수치 하나를 크게 강조. subtitle에 숫자+단위 필수"},
                {"role": "solution", "duration": 10, "hint": "이 상황에서 할 수 있는 전략 또는 대비책. '지금 당장' 실천 가능한 방법"},
                {"role": "closing",  "duration": 9,  "hint": "경제 전문가 명언 또는 역사적 교훈 인용. 큰따옴표 가능"},
                {"role": "closing",  "duration": 8,  "hint": "핵심 메시지 한 문장 + 여운. subtitle은 핵심 경제 키워드"},
                {"role": "closing",  "duration": 8,  "hint": "구독/좋아요 CTA. subtitle: '구독 클릭'"},
            ],
        },
        "longform_script_template": "longform_script_economy.txt",
        "longform_scene_format": {
            "total_scenes": 14,
            "duration_seconds": 540,
            "structure": [
                {"role": "hook",     "duration": 15, "hint": "경제 충격 수치. subtitle에 숫자+단위 필수"},
                {"role": "hook",     "duration": 15, "hint": "핵심 경제 수치 강조 씬. subtitle이 메인 비주얼"},
                {"role": "problem",  "duration": 30, "hint": "구조적 원인. 금리/인플레이션/부채/유동성 키워드"},
                {"role": "numbered", "duration": 45, "hint": "첫 번째 팩트: 데이터/통계 기반 경제 사실"},
                {"role": "stat",     "duration": 30, "hint": "관련 경제 지표 수치 강조. subtitle에 숫자 필수"},
                {"role": "numbered", "duration": 45, "hint": "두 번째 팩트: 글로벌/역사적 사례 비교"},
                {"role": "numbered", "duration": 45, "hint": "세 번째 팩트: 현재 경제와의 연결"},
                {"role": "quote",    "duration": 30, "hint": "경제학자/투자 전문가 실제 인용. 큰따옴표 필수"},
                {"role": "numbered", "duration": 45, "hint": "네 번째 팩트: 파급 효과 또는 숨겨진 진실"},
                {"role": "numbered", "duration": 45, "hint": "다섯 번째 팩트: 앞으로의 시나리오 또는 반전"},
                {"role": "stat",     "duration": 30, "hint": "미래 전망 수치. subtitle에 숫자 필수"},
                {"role": "quote",    "duration": 30, "hint": "두 번째 전문가 인용 또는 역사적 교훈. 큰따옴표 필수"},
                {"role": "closing",  "duration": 30, "hint": "핵심 메시지 + 감성적 마무리"},
                {"role": "closing",  "duration": 30, "hint": "구독/좋아요 CTA + 다음 경제 영상 예고"},
            ],
        },
    },
]

# --- 영상 설정 ---
VIDEO_CONFIG = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "shorts_max": 60,
    "longform_min": 480,
    "longform_max": 720,
}

IMAGE_STYLE = "cinematic, 4K, vertical 9:16, soft lighting, "

# --- Remotion ---
REMOTION_DIR = PROJECT_ROOT / "remotion"

# --- 캡컷 경로 (Windows) ---
CAPCUT_PATHS = [
    r"C:\Program Files\CapCut\CapCut.exe",
    r"C:\Users\{username}\AppData\Local\CapCut\Apps\CapCut.exe",
]

CAPCUT_DRAFT_DIR = (
    r"C:\Users\{username}\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft"
)


def get_api_key() -> str:
    """ANTHROPIC_API_KEY 환경변수 반환. 없으면 빈 문자열."""
    return os.environ.get("ANTHROPIC_API_KEY", "")


def allow_claude_api() -> bool:
    """Claude API 사용 허용 여부.

    기본값은 False(로컬 모드). 명시적으로 USE_CLAUDE_API=1일 때만 API 호출.
    """
    return USE_CLAUDE_API


def get_capcut_paths() -> tuple[list[str], str]:
    """캡컷 실행 파일/드래프트 경로 후보 반환.

    참고:
        os.getlogin()/USERNAME는 실제 프로필 폴더명과 다를 수 있으므로
        USERPROFILE/Path.home()를 우선 사용한다.
    """
    home_candidates: list[Path] = []

    # 실제 프로필 디렉토리 우선
    user_profile = os.environ.get("USERPROFILE", "").strip()
    if user_profile:
        home_candidates.append(Path(user_profile))

    home_candidates.append(Path.home())

    # 보조 후보 (세션 사용자명)
    username_env = os.environ.get("USERNAME", "").strip()
    if username_env:
        home_candidates.append(Path(r"C:\Users") / username_env)

    try:
        login_name = os.getlogin()
        if login_name:
            home_candidates.append(Path(r"C:\Users") / login_name)
    except OSError:
        pass

    # 중복 제거 (순서 유지)
    uniq_homes: list[Path] = []
    seen: set[str] = set()
    for h in home_candidates:
        key = str(h).lower()
        if key in seen:
            continue
        seen.add(key)
        uniq_homes.append(h)

    exe_paths: list[str] = [r"C:\Program Files\CapCut\CapCut.exe"]
    draft_candidates: list[Path] = []

    for home in uniq_homes:
        exe_paths.append(str(home / "AppData" / "Local" / "CapCut" / "Apps" / "CapCut.exe"))
        draft_candidates.append(home / "AppData" / "Local" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft")

    # 기존 템플릿 경로도 마지막 호환 후보로 유지
    if username_env:
        exe_paths.extend([p.replace("{username}", username_env) for p in CAPCUT_PATHS])
        draft_candidates.append(Path(CAPCUT_DRAFT_DIR.replace("{username}", username_env)))

    # 실행 파일 경로 중복 제거
    uniq_execs: list[str] = []
    exec_seen: set[str] = set()
    for p in exe_paths:
        key = str(p).lower()
        if key in exec_seen:
            continue
        exec_seen.add(key)
        uniq_execs.append(str(p))

    # 실제 존재하는 드래프트 폴더 우선 선택
    draft_dir = next((str(p) for p in draft_candidates if p.exists()), str(draft_candidates[0]))
    return uniq_execs, draft_dir
