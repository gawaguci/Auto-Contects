"""캡컷 draft_content.json 프로젝트 생성."""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from pathlib import Path

import config
from pipeline.script_gen import Script


def _seconds_to_us(seconds: float) -> int:
    """초 → 마이크로초 변환."""
    return int(seconds * 1_000_000)


def _generate_id() -> str:
    """고유 ID 생성."""
    return str(uuid.uuid4()).replace("-", "").upper()[:24]


def _build_materials(script: Script, job_dir: Path) -> dict:
    """materials 섹션 생성."""
    clips_dir = job_dir / "clips"
    audio_dir = job_dir / "audio"

    videos = []
    for scene in script.scenes:
        clip_path = clips_dir / f"clip_{scene.index:02d}.mp4"
        videos.append({
            "id": f"mat_video_{scene.index:02d}",
            "path": str(clip_path.resolve()),
            "duration": _seconds_to_us(scene.duration),
            "type": "video",
            "width": config.VIDEO_CONFIG["width"],
            "height": config.VIDEO_CONFIG["height"],
        })

    audios = [{
        "id": "mat_audio_full",
        "path": str((audio_dir / "full_narration.mp3").resolve()),
        "duration": _seconds_to_us(script.total_duration),
        "type": "audio",
    }]

    texts = []
    for scene in script.scenes:
        texts.append({
            "id": f"mat_text_{scene.index:02d}",
            "content": scene.subtitle,
            "font_path": "",
            "font_name": "NanumGothicBold",
            "font_size": 60,
            "font_color": "#FFFFFF",
            "border_width": 3,
            "border_color": "#000000",
        })

    return {"videos": videos, "audios": audios, "texts": texts}


def _build_tracks(script: Script) -> list[dict]:
    """tracks 섹션 생성."""
    # 비디오 트랙
    video_segments = []
    cumulative_us = 0
    for scene in script.scenes:
        dur_us = _seconds_to_us(scene.duration)
        video_segments.append({
            "material_id": f"mat_video_{scene.index:02d}",
            "target_timerange": {"start": cumulative_us, "duration": dur_us},
            "source_timerange": {"start": 0, "duration": dur_us},
            "extra_material_refs": [],
        })
        cumulative_us += dur_us

    # 오디오 트랙
    total_us = _seconds_to_us(script.total_duration)
    audio_segments = [{
        "material_id": "mat_audio_full",
        "target_timerange": {"start": 0, "duration": total_us},
        "source_timerange": {"start": 0, "duration": total_us},
    }]

    # 텍스트(자막) 트랙
    text_segments = []
    cumulative_us = 0
    for scene in script.scenes:
        dur_us = _seconds_to_us(scene.duration)
        text_segments.append({
            "material_id": f"mat_text_{scene.index:02d}",
            "target_timerange": {"start": cumulative_us, "duration": dur_us},
        })
        cumulative_us += dur_us

    return [
        {"type": "video", "segments": video_segments},
        {"type": "audio", "segments": audio_segments},
        {"type": "text", "segments": text_segments},
    ]


def _build_draft_content(script: Script, job_dir: Path) -> dict:
    """draft_content.json 전체 구조 생성."""
    return {
        "id": _generate_id(),
        "name": script.title,
        "type": "draft",
        "duration": _seconds_to_us(script.total_duration),
        "canvas_config": {
            "width": config.VIDEO_CONFIG["width"],
            "height": config.VIDEO_CONFIG["height"],
            "ratio": "original",
        },
        "materials": _build_materials(script, job_dir),
        "tracks": _build_tracks(script),
        "version": 1,
        "platform": "windows",
        "create_time": int(time.time()),
    }


def _build_draft_meta(script: Script) -> dict:
    """draft_meta_info.json 메타데이터 생성."""
    return {
        "draft_fold_path": "",
        "draft_name": script.title,
        "draft_removable_storage_device": "",
        "tm_draft_create": int(time.time()),
        "tm_draft_modified": int(time.time()),
        "tm_duration": _seconds_to_us(script.total_duration),
    }


def create_capcut_project(script: Script, job_dir: Path) -> Path:
    """캡컷 드래프트 프로젝트 생성.

    Args:
        script: 스크립트 객체
        job_dir: output/{job_id} 경로

    Returns:
        캡컷 프로젝트 디렉토리 경로
    """
    project_dir = job_dir / "capcut_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    # clips/ 누락 시 자동 생성 (캡컷 타임라인 안정성)
    clips_dir = job_dir / "clips"
    expected_clips = [clips_dir / f"clip_{scene.index:02d}.mp4" for scene in script.scenes]
    if not all(p.exists() for p in expected_clips):
        try:
            from pipeline.video_build import build_scene_clips
            build_scene_clips(script, job_dir)
            print("  캡컷용 클립 자동 생성 완료")
        except Exception as e:
            print(f"  캡컷용 클립 자동 생성 실패: {e}")
            print("  (영상/이미지 파일 경로를 캡컷에서 수동 확인해 주세요.)")

    # draft_content.json 생성
    draft_content = _build_draft_content(script, job_dir)
    content_path = project_dir / "draft_content.json"
    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(draft_content, f, ensure_ascii=False, indent=2)

    # draft_meta_info.json 생성
    meta = _build_draft_meta(script)
    meta_path = project_dir / "draft_meta_info.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Windows에서만 캡컷 드래프트 폴더로 복사
    if os.name == "nt":
        try:
            _, draft_dir = config.get_capcut_paths()
            draft_path = Path(draft_dir)
            if draft_path.exists():
                dest = draft_path / draft_content["id"]
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(project_dir, dest)
                print(f"  캡컷 드래프트 폴더에 복사 완료: {dest}")
            else:
                print(f"  캡컷 드래프트 폴더가 없습니다: {draft_dir}")
                print("  캡컷 설치 후 수동으로 프로젝트를 열어주세요.")
        except Exception as e:
            print(f"  캡컷 드래프트 복사 실패: {e}")
    else:
        print("  (Linux 환경) 캡컷 프로젝트가 로컬에 생성되었습니다.")
        print(f"  Windows에서 {project_dir} 폴더를 캡컷 드래프트 폴더에 복사하세요.")

    return project_dir
