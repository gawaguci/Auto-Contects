"""YouTube 영상 자동화 파이프라인 CLI 진입점."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import config
from pipeline.file_naming import build_video_filename


def _next_job_id(output_dir: Path) -> str:
    """오늘 날짜 기반 순차 job_id 생성."""
    today = datetime.now().strftime("%Y%m%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(output_dir.glob(f"{today}_*"))
    seq = len(existing) + 1
    return f"{today}_{seq:03d}"


def _select_number(prompt: str, min_val: int, max_val: int, default: int | None = None) -> int:
    """사용자로부터 번호 입력 받기."""
    while True:
        try:
            raw = input(prompt).strip()
            if not raw and default is not None:
                return default
            num = int(raw)
            if min_val <= num <= max_val:
                return num
            print(f"  {min_val}~{max_val} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("  숫자를 입력하세요.")
        except (EOFError, KeyboardInterrupt):
            print("\n취소되었습니다.")
            sys.exit(0)


def _run_step(step_num: int, total: int, label: str, func, *args, **kwargs):
    """파이프라인 단계 실행 + 재시도."""
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            print(f"[{step_num}/{total}] {label}...", end="", flush=True)
            result = func(*args, **kwargs)
            print(f"  \u2705 완료")
            return result
        except Exception as e:
            print(f"  \u274c 실패: {e}")
            if attempt < max_retries:
                try:
                    retry = input("  재시도? (y/n): ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    retry = "n"
                if retry != "y":
                    raise
            else:
                raise


def _configure_stdio() -> None:
    """Windows cp949 콘솔에서도 이모지 출력이 죽지 않도록 UTF-8 강제."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_job_status(status_file: Path, payload: dict) -> None:
    """job_status.json 갱신.

    Windows에서 파일 잠금(백신/인덱서/읽기 경합)으로 os.replace가 간헐 실패할 수 있어
    짧은 재시도 후 최종 폴백(직접 덮어쓰기)을 수행한다.
    """
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    attempts = 5
    for i in range(attempts):
        tmp = status_file.with_name(f"{status_file.stem}.{os.getpid()}.tmp")
        try:
            tmp.write_text(data, encoding="utf-8")
            os.replace(str(tmp), str(status_file))
            return
        except PermissionError:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            if i < attempts - 1:
                time.sleep(0.05 * (i + 1))
                continue
            # 최종 폴백: 원본 직접 덮어쓰기
            status_file.write_text(data, encoding="utf-8")
            return


_IMAGE_STYLE_OPTIONS = [
    "화풍 없음 (기본)",
    "시네마틱 실사",
    "수채화",
    "카툰/만화",
    "애니메이션",
    "유화",
    "연필 스케치",
    "흰 얼굴 캐릭터",
]


def _render_mode_label(mode: str) -> str:
    labels = {
        "auto": "자동 렌더링",
        "studio": "Remotion Studio",
        "capcut": "캡컷 프로젝트",
    }
    return labels.get(mode, mode)


def _auto_mode(args) -> tuple:
    """--auto 플래그로 전달된 인자에서 파이프라인 파라미터 추출."""
    # 카테고리
    cat_id = args.category
    matching = [c for c in config.CATEGORIES if c["id"] == cat_id]
    if not matching:
        print(f"오류: 카테고리 ID {cat_id}가 존재하지 않습니다.")
        sys.exit(1)
    category = matching[0]

    # 주제: --topic 으로 직접 전달 (topic 객체 흉내)
    class TopicObj:
        def __init__(self, title: str):
            self.title = title
            self.index = 1
            self.hook = title
            self.trend = ""
            self.keywords = []
    topic = TopicObj(args.topic)

    # 버전
    version = args.type  # 'shorts' | 'longform'

    # 언어 (script_gen/tts_gen에서 사용)
    language = args.language  # 'ko' | 'en'

    # TTS
    tts_provider = args.tts  # 'edge-tts' | 'elevenlabs' | 'typecast'

    # 이미지 스타일 인덱스
    image_style = args.image_style

    # 렌더링 방식
    render_mode = args.render  # 'auto' | 'studio' | 'capcut'

    return category, topic, version, language, tts_provider, image_style, render_mode


def main():
    """메인 CLI 흐름."""
    _configure_stdio()

    parser = argparse.ArgumentParser(description="YouTube 영상 자동화 파이프라인")
    parser.add_argument(
        "--legacy", action="store_true",
        help="기존 FFmpeg+Pillow 방식으로 렌더링 (Remotion 대신)",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Web UI / AI auto mode (no interactive input)",
    )
    parser.add_argument("--category", type=int, default=1, help="카테고리 ID (1~6)")
    parser.add_argument("--topic", type=str, default="", help="주제 제목")
    parser.add_argument("--type", type=str, default="shorts", choices=["shorts", "longform"])
    parser.add_argument("--language", type=str, default="ko", choices=["ko", "en"])
    parser.add_argument("--tts", type=str, default="edge-tts", choices=["edge-tts", "elevenlabs", "typecast"])
    parser.add_argument("--image-style", type=int, default=0, dest="image_style")
    parser.add_argument("--render", type=str, default="auto", choices=["auto", "studio", "capcut"])
    args = parser.parse_args()
    use_legacy = args.legacy

    if args.auto:
        # === 자동 모드 (Web UI / AI 대화 모드) ===
        category, topic, version, language, tts_provider, image_style, render_mode = _auto_mode(args)
        print()
        print("=" * 50)
        print(f"  YouTube 영상 자동화 파이프라인 [AUTO]")
        print("=" * 50)
        print(f"  카테고리: {category['emoji']} {category['name']}")
        print(f"  주제: {topic.title}")
        print(f"  버전: {version} / 언어: {language} / TTS: {tts_provider}")
        print(f"  이미지 스타일: {image_style} / 렌더: {_render_mode_label(render_mode)}")
        print()
    else:
        print()
        print("=" * 50)
        renderer = "FFmpeg+Pillow (Legacy)" if use_legacy else "Remotion"
        print(f"  YouTube 영상 자동화 파이프라인  [{renderer}]")
        print("=" * 50)
        print()

        # === 카테고리 선택 ===
        print("=== 카테고리 선택 ===")
        for cat in config.CATEGORIES:
            print(f"  {cat['id']}. {cat['emoji']} {cat['name']} - {cat['desc']}")
        print()

        n_cats = len(config.CATEGORIES)
        cat_idx = _select_number(f"선택 (1~{n_cats}): ", 1, n_cats)
        category = config.CATEGORIES[cat_idx - 1]
        print(f"\n  \u279c {category['emoji']} {category['name']} 선택됨\n")

        # === 주제 조사 ===
        print(f"\U0001f50d 요즘 핫한 {category['name']} 주제 조사 중...")
        from pipeline.topic_gen import generate_topics
        topics = generate_topics(category)

        print()
        print("=== 주제 선택 ===")
        for t in topics:
            print(f"  {t.index}. {t.title}")
            print(f"     \U0001f525 {t.trend}")
        print()

        topic_idx = _select_number("선택 (1~5): ", 1, len(topics))
        topic = topics[topic_idx - 1]
        print(f"\n  \u279c \"{topic.title}\" 선택됨\n")

        # === 영상 버전 선택 ===
        print("=== 영상 버전 ===")
        print("  1. \U0001f3ac 쇼츠 (90초) \u2190 기본")
        print("  2. \U0001f3ac 롱폼 (8~12분)")
        print()

        version_idx = _select_number("선택 (엔터=1): ", 1, 2, default=1)
        version = "shorts" if version_idx == 1 else "longform"
        version_label = "쇼츠" if version == "shorts" else "롱폼"
        print(f"\n  \u279c {version_label} 선택됨\n")

        # === 언어 선택 ===
        print("=== 언어 ===")
        print("  1. \U0001f1f0\U0001f1f7 한국어 \u2190 기본")
        print("  2. \U0001f1fa\U0001f1f8 영어")
        print()

        language_idx = _select_number("선택 (엔터=1): ", 1, 2, default=1)
        language = "ko" if language_idx == 1 else "en"
        print(f"\n  \u279c {'한국어' if language == 'ko' else '영어'} 선택됨\n")

        # === TTS 공급자 선택 ===
        print("=== TTS 공급자 ===")
        print("  1. Edge-TTS (무료) \u2190 기본")
        print("  2. ElevenLabs (유료)")
        print("  3. Typecast (유료)")
        print()

        tts_idx = _select_number("선택 (엔터=1): ", 1, 3, default=1)
        tts_provider = "edge-tts" if tts_idx == 1 else "elevenlabs" if tts_idx == 2 else "typecast"
        print(f"\n  \u279c {tts_provider} 선택됨\n")

        # === 이미지 스타일 선택 ===
        print("=== 이미지 스타일 ===")
        for idx, name in enumerate(_IMAGE_STYLE_OPTIONS):
            default_mark = " \u2190 기본" if idx == 0 else ""
            print(f"  {idx}. {name}{default_mark}")
        print()
        image_style = _select_number("선택 (엔터=0): ", 0, len(_IMAGE_STYLE_OPTIONS) - 1, default=0)
        print(f"\n  \u279c {_IMAGE_STYLE_OPTIONS[image_style]} 선택됨\n")

        # === 렌더링 방식 선택 ===
        if not use_legacy:
            print("=== 렌더링 방식 ===")
            print("  1. \u26a1 자동 렌더링 (Remotion \u2192 mp4 파일) \u2190 기본")
            print("  2. \U0001f3db  Remotion Studio (직접 렌더링)")
            print("  3. \u2702\ufe0f 캡컷 프로젝트 (Remotion 렌더 없음)")
            print()
            render_idx = _select_number("선택 (엔터=1): ", 1, 3, default=1)
            render_mode = "auto" if render_idx == 1 else "studio" if render_idx == 2 else "capcut"
            render_label = _render_mode_label(render_mode)
            print(f"\n  \u279c {render_label} 선택됨\n")
        else:
            render_mode = "auto"

    # === 파이프라인 실행 ===
    job_id = _next_job_id(config.OUTPUT_DIR)
    job_dir = config.OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    status_file = job_dir / "job_status.json"

    print(f"Job ID: {job_id}")
    print(f"출력 경로: {job_dir}")
    print()

    if use_legacy:
        total_steps = 6
    elif render_mode == "capcut":
        total_steps = 5
    else:
        total_steps = 5

    status_base = {
        "job_id": job_id,
        "pid": os.getpid(),
        "started_at": _now_iso(),
    }
    current_step = "초기화"
    completed_steps = 0

    def set_status(status: str, **extra) -> None:
        payload = {
            **status_base,
            "status": status,
            "step": current_step,
            "updated_at": _now_iso(),
            "progress": {"current": completed_steps, "total": total_steps},
            **extra,
        }
        _write_job_status(status_file, payload)

    try:
        set_status("running")

        # [1] 스크립트 생성
        current_step = "스크립트 생성"
        set_status("running")
        from pipeline.script_gen import generate_script
        script = _run_step(
            1, total_steps,
            f"\U0001f4dd 스크립트 생성 중",
            generate_script, topic, category, version, 2, language,
        )
        completed_steps = 1
        video_filename = build_video_filename(script.title)
        output_video_hint = video_filename if render_mode != "capcut" else None
        set_status("running", output_video=output_video_hint, render_mode=render_mode)
        print(f"     {len(script.scenes)}장면 / {script.total_duration:.0f}초")

        # [2] TTS 음성 생성
        current_step = "TTS 음성 생성"
        set_status("running", output_video=output_video_hint, render_mode=render_mode)
        from pipeline.tts_gen import generate_tts, _generate_subtitles
        script = _run_step(
            2, total_steps,
            f"\U0001f399\ufe0f  TTS 음성 생성 중 ({tts_provider})",
            generate_tts, script, category, job_dir, tts_provider, language,
        )
        completed_steps = 2
        set_status("running", output_video=output_video_hint, render_mode=render_mode)
        rate = category["shorts_rate"] if version == "shorts" else category["longform_rate"]
        print(f"     {tts_provider} / {script.total_duration:.1f}초")

        # 자막 파일 생성 (TTS 완료 직후 — 타이밍 기반)
        _generate_subtitles(script, job_dir)

        if use_legacy:
            # --- Legacy 모드: 기존 FFmpeg+Pillow ---
            # [3/6] 이미지 생성
            current_step = "이미지 생성"
            set_status("running", output_video=output_video_hint, render_mode=render_mode)
            from pipeline.image_gen import generate_images
            image_paths = _run_step(
                3, total_steps,
                "\U0001f3a8 이미지 생성 중",
                generate_images, script, category, job_dir, image_style,
            )
            completed_steps = 3
            set_status("running", output_video=output_video_hint, render_mode=render_mode)
            print(f"     {len(image_paths)}장 / {config.VIDEO_CONFIG['width']}x{config.VIDEO_CONFIG['height']}")

            # [4/6] FFmpeg 영상 조합
            current_step = "영상 조합"
            set_status("running", output_video=output_video_hint, render_mode=render_mode)
            from pipeline.video_build import build_video
            final_path = _run_step(
                4, total_steps,
                "\U0001f3ac FFmpeg 영상 조합 중",
                build_video, script, job_dir, video_filename,
            )
            completed_steps = 4
            set_status("running", output_video=output_video_hint, render_mode=render_mode)
            print(f"     {final_path.name}")

            next_step = 5
        else:
            if render_mode == "capcut":
                # --- 캡컷 전용 모드 ---
                current_step = "캡컷용 이미지/클립 생성"
                set_status("running", output_video=None, render_mode=render_mode)
                from pipeline.remotion_render import prepare_scene_images
                from pipeline.video_build import build_scene_clips
                image_paths = _run_step(
                    3, total_steps,
                    "\U0001f5bc\ufe0f  캡컷용 이미지 준비 중",
                    prepare_scene_images, script, category, job_dir, image_style,
                )
                clip_paths = _run_step(
                    3, total_steps,
                    "\U0001f39e\ufe0f  캡컷용 클립 생성 중",
                    build_scene_clips, script, job_dir,
                )
                print(f"     이미지 {len(image_paths)}장 / 클립 {len(clip_paths)}개")
                final_path = None
                completed_steps = 3
                set_status("running", output_video=None, render_mode=render_mode)
                next_step = 4
            else:
                # --- Remotion 모드 (auto/studio) ---
                current_step = "렌더링"
                set_status("running", output_video=output_video_hint, render_mode=render_mode)
                if render_mode == "studio":
                    # [3/5] Remotion Studio 수동 렌더링
                    from pipeline.remotion_render import open_studio
                    _run_step(
                        3, total_steps,
                        "\U0001f3db  Remotion Studio 실행 중",
                        open_studio, script, category, job_dir, video_filename, image_style,
                    )
                    final_path = job_dir / video_filename
                else:
                    # [3/5] Remotion 자동 렌더링
                    from pipeline.remotion_render import render_video
                    final_path = _run_step(
                        3, total_steps,
                        "\U0001f3ac Remotion 자동 렌더링 중",
                        render_video, script, category, job_dir, version, 4, video_filename, image_style,
                    )
                    print(f"     {final_path.name}")

                completed_steps = 3
                set_status("running", output_video=output_video_hint, render_mode=render_mode)
                next_step = 4

        # 캡컷 프로젝트 생성
        current_step = "캡컷 프로젝트 생성"
        set_status("running", output_video=output_video_hint, render_mode=render_mode)
        from pipeline.capcut_project import create_capcut_project
        project_dir = _run_step(
            next_step, total_steps,
            "\U0001f39e\ufe0f  캡컷 프로젝트 생성 중",
            create_capcut_project, script, job_dir,
        )
        completed_steps = next_step
        set_status("running", output_video=output_video_hint, render_mode=render_mode)
        print(f"     draft_content.json")

        # 캡컷 자동 실행
        current_step = "캡컷 실행"
        set_status("running", output_video=output_video_hint, render_mode=render_mode)
        from pipeline.capcut_launcher import launch_capcut
        print(f"[{next_step + 1}/{total_steps}] \U0001f680 캡컷 자동 실행 중...", end="", flush=True)
        launched = launch_capcut(project_dir)
        completed_steps = total_steps
        if launched:
            print(f"  \u2705 프로젝트 로드 완료")
        else:
            print()

        set_status(
            "completed",
            output_video=final_path.name if final_path else None,
            capcut_launched=launched,
            render_mode=render_mode,
        )

        # === 완료 ===
        print()
        print("=" * 50)
        print(f"  \U0001f389 완료!")
        print("=" * 50)
        print()
        print(f"  \U0001f4c1 {job_dir}/")
        if final_path:
            render_note = "Remotion Studio 수동 렌더링" if (not use_legacy and render_mode == "studio") else "Remotion 완성본"
            print(f"     \u251c\u2500\u2500 {final_path.name}              \u2190 {render_note}")
        else:
            print(f"     \u251c\u2500\u2500 (mp4 없음)             \u2190 캡컷 프로젝트 모드")
        print(f"     \u251c\u2500\u2500 clips/                 \u2190 캡컷용 씬 클립")
        print(f"     \u251c\u2500\u2500 audio/                 \u2190 TTS 음성")
        print(f"     \u251c\u2500\u2500 images/                \u2190 장면 이미지")
        print(f"     \u2514\u2500\u2500 capcut_project/        \u2190 캡컷 드래프트")
        print()

        if not launched:
            print("  \u25b6 캡컷에서 프로젝트를 열고 \"내보내기\" 버튼을 누르세요.")
        else:
            print("  \u25b6 캡컷에서 \"내보내기\" 버튼만 누르면 완료!")
        print()
    except KeyboardInterrupt:
        set_status("stopped", error="사용자 중단")
        raise
    except Exception as e:
        set_status(
            "failed",
            error=str(e),
            traceback=traceback.format_exc(limit=8),
        )
        raise


if __name__ == "__main__":
    main()
