# Auto-Contects — 유튜브 영상 자동 생성 파이프라인

## 프로젝트 개요

카테고리 선택부터 최종 영상 렌더링까지, 유튜브 쇼츠/롱폼 영상을 자동으로 생성하는 파이프라인입니다.

---

## 디렉토리 구조

```
Auto-Contects/
│
├── _run_pipeline.py          # 유일한 진입점 — 전체 파이프라인 실행
├── _topics_for_ui.py         # 웹UI용 주제 생성 헬퍼
├── config.py                 # 카테고리/보이스/스타일 등 모든 설정값
├── requirements.txt          # Python 의존성
├── .env                      # API 키 (Gemini, ElevenLabs, Typecast 등)
│
├── pipeline/                 # 파이프라인 모듈
│   ├── topic_gen.py          # 주제 생성
│   ├── script_gen.py         # 스크립트 생성
│   ├── metadata_gen.py       # 메타데이터 생성 (제목/태그/해시태그)
│   ├── image_gen.py          # 배경 이미지 생성 (Gemini AI)
│   ├── stock_image.py        # 스톡 이미지 수집 (Pexels/Pixabay)
│   ├── tts_gen.py            # TTS 음성 생성 (edge-tts / ElevenLabs / Typecast)
│   ├── remotion_render.py    # Remotion 렌더링
│   ├── video_build.py        # 영상 빌드 조율
│   ├── capcut_project.py     # 캡컷 프로젝트 생성
│   ├── capcut_launcher.py    # 캡컷 자동 실행
│   └── file_naming.py        # 출력 파일명 규칙
│
├── templates/                # 스크립트 생성 프롬프트 템플릿
│   ├── shorts_script_psychology.txt
│   ├── shorts_script_history.txt
│   ├── shorts_script_brain.txt
│   ├── shorts_script_korean_history.txt
│   ├── shorts_script_money.txt
│   ├── shorts_script_economy.txt
│   ├── longform_script_psychology.txt
│   ├── longform_script_history.txt
│   ├── longform_script_brain.txt
│   ├── longform_script_korean_history.txt
│   ├── longform_script_money.txt
│   ├── longform_script_economy.txt
│   ├── shorts_script_prompt.txt
│   ├── longform_script_prompt.txt
│   └── topic_search_prompt.txt
│
├── remotion/                 # Remotion 영상 렌더러 (React)
│   └── src/
│       ├── index.ts
│       ├── Root.tsx
│       └── VideoComposition.tsx
│
├── web/                      # Next.js 웹 대시보드
│   └── app/
│       ├── page.tsx              # 메인 페이지
│       ├── generate/page.tsx     # 영상 생성 화면
│       ├── jobs/page.tsx         # 작업 목록
│       ├── api/generate/route.ts # 생성 API
│       ├── api/topics/route.ts   # 주제 API
│       ├── lib/
│       │   ├── jobs.ts           # 작업 관리
│       │   └── categories.ts     # 카테고리 정의
│       └── design-system/        # 디자인 시스템 (토큰/컴포넌트)
│
├── output/                   # 생성 결과물
│   └── {job_id}/
│       ├── final.mp4
│       ├── thumbnail.png
│       ├── metadata.json
│       ├── subtitles.srt
│       └── audio/
│           ├── full_narration.mp3
│           └── scene_01.mp3 ~ scene_10.mp3
│
└── tests/                    # 테스트
```

---

## 생성 파이프라인

| 단계 | 내용 |
|------|------|
| ① 카테고리 선택 | 심리학 / 역사 충격 / 뇌과학 / 한국사 X파일 / 돈의 심리학 / 경제 다큐 |
| ② 주제 생성/선택 | 주제 5개 자동 생성 후 선택 |
| ③ 영상 버전 선택 | 쇼츠(90초) / 롱폼(10분) |
| ④ 언어 선택 | 한국어 / 영어 |
| ⑤ TTS 공급자 선택 | edge-tts (무료) / ElevenLabs (유료) / Typecast (유료) |
| ⑥ 이미지 스타일 선택 | 시네마틱 실사 / 수채화 / 카툰 / 애니메이션 / 유화 / 연필 스케치 / 커스텀 등 |
| ⑦ 렌더링 방식 선택 | 자동 렌더링 / Remotion Studio / 캡컷 프로젝트 |
| ⑧ 스크립트 생성 | 카테고리 템플릿 기반 10장면 생성 |
| ⑨ 메타데이터 + 이미지 생성 | 제목/태그/해시태그 + 배경 이미지 (병렬) |
| ⑩ TTS 음성 생성 | scene_01~10.mp3 + full_narration.mp3 + subtitles.srt |
| ⑪ 배경 이미지 수집 | Pexels / Pixabay / AI 생성 |
| ⑫ Remotion 렌더링 | remotion_input.json → final.mp4 |
| ⑬ 썸네일 생성 | thumbnail.png (1080x1920) |
| ⑭ 캡컷 프로젝트 생성 + 자동 실행 | |

---

## 카테고리별 설정

| ID | 카테고리 | 보이스 |
|----|---------|--------|
| 1 | 심리학 | ko-KR-SunHiNeural |
| 2 | 역사 충격 | ko-KR-InJoonNeural |
| 3 | 뇌과학 | ko-KR-SunHiNeural |
| 4 | 한국사 X파일 | ko-KR-InJoonNeural |
| 5 | 돈의 심리학 | ko-KR-InJoonNeural |
| 6 | 경제 다큐 | ko-KR-InJoonNeural |

---

## 실행 방법

### AI 대화 방식 (권장)
Claude Code에서 아래 트리거 입력 후 단계별 선택:
```
유튜브 영상 생성해줘
```

### 수동 실행
```bash
python _run_pipeline.py
```

### 자동 실행 (인자 지정)
```bash
python _run_pipeline.py --auto --category 1 --version shorts --lang ko --tts edge-tts --style 1 --render auto
```

---

## 환경 설정

`.env` 파일에 아래 키를 설정합니다:

```
GEMINI_API_KEY=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
```

의존성 설치:
```bash
pip install -r requirements.txt
```

