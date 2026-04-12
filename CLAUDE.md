# 유튜브 영상 자동 생성 파이프라인

## ⚠️ Windows 실행 환경 규칙 (절대 위반 금지)
- **주제 생성 포함 모든 Python 실행은 `_run_pipeline.py --auto ...` 하나로만 한다.** 내부 모듈(topic_gen, script_gen 등)을 직접 호출하지 말 것
- Bash 툴에서 `cd` 명령 사용 금지 — 현재 디렉토리는 항상 `/c/Myproject/shorts-auto`이다
- Python 스크립트를 별도로 작성해서 실행하는 방식 금지 — `_run_pipeline.py`가 유일한 진입점이다
- Windows cp949 인코딩 문제를 우회하려고 `io.TextIOWrapper` 등을 추가하는 임시방편 금지

## ⚠️ 강제 실행 규칙 (절대 위반 금지)
- 사용자가 `유튜브 영상 생성해줘` 또는 `유튜브 영상 생성해줘:` 라고 입력하면, 그 문장을 **워크플로우 시작 트리거**로 간주한다.
- 위 트리거가 들어오면 설명/준비 문장/터미널 실행 안내 없이 **즉시 ① 카테고리 선택부터 시작**한다.
- 파이프라인 ①~⑬ 순서를 **한 단계씩** 반드시 지킬 것
- 사용자가 선택하기 전에 절대 다음 단계로 넘어가지 말 것
- 절차를 건너뛰거나 한꺼번에 묻지 말 것
- ①~⑦은 모두 **대화에서 한 단계씩** 선택을 받은 뒤 `_run_pipeline.py --auto` 인자로 반영한다.
- 사용자가 각 단계를 고를 수 있게 **매 단계마다 선택지를 직접 보여주고**, 답을 받기 전에는 다음 단계로 넘어가지 말 것.
- 사용자가 직접 터미널에서 `_run_pipeline.py`를 실행하게 떠넘기지 말 것. 선택이 끝나면 AI가 `_run_pipeline.py --auto ...`로 실행한다.
- **카테고리 source of truth는 `config.py`의 `CATEGORIES` 하나뿐이다.** 카테고리 이름/개수는 기억이나 요약본이 아니라 반드시 여기 기준으로 따른다.
- **카테고리 선택 시 버튼형/퀵픽/체크박스형 선택 UI를 쓰지 말 것.** 일부 대화 UI가 4개까지만 버튼으로 노출하므로, 5개 이상 선택지는 반드시 사용자가 `번호 또는 카테고리명`을 직접 입력하게 해야 한다.
- ① 카테고리 질문은 아래 형식을 그대로 사용한다.  
  `카테고리를 직접 입력해주세요 (번호 또는 이름): 1 심리학, 2 역사 충격, 3 뇌과학, 4 한국사 X파일, 5 돈의 심리학, 6 경제 다큐`
- ② 주제 선택은 주제 5개를 보여준 뒤 직접 입력 방식으로 묻는다.  
  `주제를 직접 입력해주세요 (번호 또는 이름). 다시 생성하려면 0 또는 다시 입력`
- ③ 영상 버전 질문도 버튼형 UI 대신 직접 입력 방식으로 묻는다.  
  `영상 버전을 직접 입력해주세요 (번호 또는 이름): 1 쇼츠, 2 롱폼`
- ④ 언어 질문도 직접 입력 방식으로 묻는다.  
  `언어를 직접 입력해주세요 (번호 또는 이름): 1 한국어, 2 영어`
- ⑤ TTS 공급자 질문도 직접 입력 방식으로 묻는다.  
  `TTS 공급자를 직접 입력해주세요 (번호 또는 이름): 1 edge-tts, 2 ElevenLabs`
- ⑥ 이미지 스타일 질문도 직접 입력 방식으로 묻는다.  
  `이미지 스타일을 직접 입력해주세요 (번호 또는 이름): 0 화풍 없음, 1 시네마틱 실사, 2 수채화, 3 카툰/만화, 4 애니메이션, 5 유화, 6 연필 스케치, 7 흰 얼굴 캐릭터, 8 커스텀 직접 입력`
- ⑦ 렌더링 방식 질문도 직접 입력 방식으로 묻는다.  
  `렌더링 방식을 직접 입력해주세요 (번호 또는 이름): 1 자동 렌더링, 2 Remotion Studio, 3 캡컷 프로젝트, 4 Remotion 고속 모드`
- topic_override.json / script_override.json 등 파일 주입으로 순서를 바꾸는 편법 금지
- 사용자 명시적 지시 없이는 절대 순서 변경 금지
- "형들 잠깐만 들어봐" 등 타 채널 저작권 문구 사용 금지
- **Claude API(anthropic 라이브러리) 코드 내 직접 호출 절대 금지** — AI는 Claude Code(나) 자신이며, 파이프라인 코드에서 anthropic SDK를 import하거나 호출하지 말 것

---

## 생성 파이프라인 (순서 절대 엄수)

```
START
  │
  ▼
① 카테고리 선택
  │  1. 🧠 심리학
  │  2. ⚡ 역사 충격
  │  3. 🔬 뇌과학
  │  4. 📜 한국사 X파일
  │  5. 💰 돈의 심리학
  │  6. 📊 경제 다큐
  ▼
② 주제 생성 / 선택
  │  Claude API → 주제 5개 생성
  │  1~5 선택 or "다시" 재생성
  ▼
③ 영상 버전 선택
  │  1. 쇼츠 (90초) ← 기본
  │  2. 롱폼 (10분)
  ▼
④ 언어 선택
  │  1. 한국어 ← 기본
  │  2. 영어
  ▼
⑤ TTS 공급자 선택
  │  1. edge-tts (무료) ← 기본
  │  2. ElevenLabs (유료) → .env에서 Voice ID/Model 자동 로드
  ▼
⑥ 이미지 스타일 선택
  │  0. 화풍 없음 (카테고리 기본) ← 기본
  │  1. 시네마틱 실사
  │  2. 수채화
  │  3. 카툰/만화
  │  4. 애니메이션
  │  5. 유화
  │  6. 연필 스케치
  │  7. 흰 얼굴 캐릭터 (참조 영상 스타일)
  │  8. 커스텀 직접 입력
  ▼
⑦ 렌더링 방식 선택
  │  1. 자동 렌더링 (Remotion → final.mp4) ← 기본
  │  2. Remotion Studio (수동 렌더링)
  ▼
⑧ 스크립트 생성 (10장면)
  │  카테고리별 템플릿 + Claude API
  │
  ├──────────────────────────────┐
  ▼                              ▼ (병렬)
⑨ 메타데이터 생성            ⑨' 배경 이미지 생성
  │  제목/태그/해시태그           │  Gemini API / Pexels / Pixabay
  │  → metadata.json            │  선택한 이미지 스타일 적용
  ▼                              │
⑩ TTS 음성 생성                  │
  │  scene_01~10.mp3            │
  │  full_narration.mp3         │
  │  subtitles.srt              │
  ▼                              │
⑪ 배경 이미지 수집 ◀─────────────┘
  ▼
⑫ 렌더링 (Remotion)
  │  remotion_input.json 생성
  │  자막 검증 (30자 초과 경고)
  │
  ├─ 자동   → npx remotion render → final.mp4
  └─ Studio → npx remotion studio → 수동 렌더링
  ▼
⑬ 썸네일 생성
  │  → thumbnail.png (1080x1920)
  ▼
⑭ 캡컷 프로젝트 생성 + 자동 실행
  ▼
END
  output/{job_id}/
    ├─ final.mp4
    ├─ thumbnail.png
    ├─ metadata.json
    ├─ subtitles.srt
    └─ audio/
        ├─ full_narration.mp3
        └─ scene_01.mp3 ~ scene_10.mp3
```

---

## 실행 방법
- AI가 대화에서 ①~⑦ 선택을 모두 받은 뒤 실행할 때: `python _run_pipeline.py --auto ...`
- 사용자가 수동으로 직접 실행할 때만: `python _run_pipeline.py`

## 카테고리별 설정 (config.py)
| ID | 카테고리 | 보이스 | 템플릿 |
|----|---------|--------|--------|
| 1 | 심리학 | ko-KR-SunHiNeural | shorts_script_psychology.txt |
| 2 | 역사 충격 | ko-KR-InJoonNeural | shorts_script_history.txt |
| 3 | 뇌과학 | ko-KR-SunHiNeural | shorts_script_brain.txt |
| 4 | 한국사 X파일 | ko-KR-InJoonNeural | shorts_script_korean_history.txt |
| 5 | 돈의 심리학 | ko-KR-InJoonNeural | shorts_script_money.txt |
| 6 | 경제 다큐 | ko-KR-InJoonNeural | shorts_script_economy.txt |

## 참조 영상 스타일 가이드
- 참조 파일: `ref/ref_subtitle_style.mp4` (경제 편의점 채널)
- 자막: 흰색 텍스트 + 검은 외곽선, 배경 없음, 44px
- 캐릭터: 흰 둥근 머리 no-face 캐릭터 → 이미지 스타일 7번 선택
