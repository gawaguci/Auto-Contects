"""FFmpeg 기반 영상 조합 (이미지+오디오+자막 → MP4)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import config
from pipeline.file_naming import build_video_filename
from pipeline.script_gen import Script


def _escape_drawtext(text: str) -> str:
    """FFmpeg drawtext 필터용 특수문자 이스케이프."""
    # FFmpeg drawtext에서 이스케이프 필요한 문자들
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "'\\''")
    text = text.replace(":", "\\:")
    text = text.replace("%", "%%")
    return text


def _find_font_path() -> str:
    """자막용 폰트 경로 탐색."""
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:\\Windows\\Fonts\\NanumGothicBold.ttf",
        "C:\\Windows\\Fonts\\malgunbd.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    return ""


def _build_scene_clip(
    image_path: Path,
    duration: float,
    output_path: Path,
    fps: int = 30,
) -> None:
    """이미지 → Ken Burns 줌인 효과 클립 생성."""
    width = config.VIDEO_CONFIG["width"]
    height = config.VIDEO_CONFIG["height"]
    total_frames = int(duration * fps)

    # zoompan: 1.0 → 1.02 서서히 줌인
    zoom_increment = 0.02 / max(total_frames, 1)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", (
            f"zoompan=z='min(zoom+{zoom_increment:.8f},1.02)'"
            f":d={total_frames}:s={width}x{height}:fps={fps},"
            f"format=yuv420p"
        ),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"클립 생성 실패 ({image_path.name}): {result.stderr[-500:]}")


def _concat_clips_with_fade(
    clip_paths: list[Path],
    durations: list[float],
    output_path: Path,
    fade_duration: float = 0.3,
) -> None:
    """클립 연결 + 페이드 전환."""
    if len(clip_paths) == 1:
        # 1개 클립이면 그냥 복사
        import shutil
        shutil.copy2(clip_paths[0], output_path)
        return

    # xfade 필터 체인 구성
    inputs = []
    for clip in clip_paths:
        inputs.extend(["-i", str(clip)])

    # xfade 필터 체인: [0][1]xfade → [v01], [v01][2]xfade → [v012], ...
    filter_parts = []
    prev_label = "[0:v]"
    cumulative_time = 0.0

    for i in range(1, len(clip_paths)):
        cumulative_time += durations[i - 1] - fade_duration
        out_label = f"[v{i}]"
        filter_parts.append(
            f"{prev_label}[{i}:v]xfade=transition=fade"
            f":duration={fade_duration}:offset={cumulative_time:.3f}{out_label}"
        )
        prev_label = out_label

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", prev_label,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        # fallback: 페이드 없이 concat
        _concat_clips_simple(clip_paths, output_path)


def _concat_clips_simple(clip_paths: list[Path], output_path: Path) -> None:
    """페이드 없이 단순 연결 (fallback)."""
    list_file = output_path.parent / "video_concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for clip in clip_paths:
            f.write(f"file '{clip.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    list_file.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"클립 연결 실패: {result.stderr[-500:]}")


def _add_audio_and_subtitles(
    video_path: Path,
    audio_path: Path,
    script: Script,
    output_path: Path,
    font_path: str,
) -> None:
    """영상에 오디오 + 자막 오버레이."""
    height = config.VIDEO_CONFIG["height"]

    # drawtext 필터: 각 장면 자막을 시간대별 표시
    subtitle_filters = []
    cumulative_time = 0.0

    for scene in script.scenes:
        escaped_text = _escape_drawtext(scene.subtitle)
        start = cumulative_time
        end = cumulative_time + scene.duration

        if font_path:
            font_part = f"fontfile='{font_path}':"
        else:
            font_part = ""

        subtitle_filters.append(
            f"drawtext=text='{escaped_text}':"
            f"{font_part}"
            f"fontsize=60:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y={int(height * 0.83)}:"
            f"enable='between(t,{start:.2f},{end:.2f})'"
        )
        cumulative_time += scene.duration

    filter_str = ",".join(subtitle_filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-filter_complex", f"[0:v]{filter_str}[vout]",
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        # fallback: 자막 없이 오디오만 합성
        _add_audio_only(video_path, audio_path, output_path)


def _add_audio_only(video_path: Path, audio_path: Path, output_path: Path) -> None:
    """자막 없이 오디오만 합성 (fallback)."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"오디오 합성 실패: {result.stderr[-500:]}")


def build_scene_clips(script: Script, job_dir: Path) -> list[Path]:
    """씬 이미지로 clip_XX.mp4 파일들을 생성."""
    clips_dir = job_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    images_dir = job_dir / "images"
    fps = config.VIDEO_CONFIG["fps"]

    clip_paths: list[Path] = []
    for scene in script.scenes:
        image_path = images_dir / f"scene_{scene.index:02d}.png"
        if not image_path.exists():
            # png 외 확장자로 저장된 경우도 허용
            candidates = sorted(images_dir.glob(f"scene_{scene.index:02d}.*"))
            if candidates:
                image_path = candidates[0]
        if not image_path.exists():
            raise FileNotFoundError(f"씬 이미지 없음: scene_{scene.index:02d}.*")

        clip_path = clips_dir / f"clip_{scene.index:02d}.mp4"
        _build_scene_clip(image_path, scene.duration, clip_path, fps)
        clip_paths.append(clip_path)

    return clip_paths


def build_video(
    script: Script,
    job_dir: Path,
    output_filename: str | None = None,
) -> Path:
    """전체 영상 빌드.

    Args:
        script: TTS 후 duration이 업데이트된 스크립트
        job_dir: output/{job_id} 경로

    Returns:
        최종 영상 경로
    """
    audio_dir = job_dir / "audio"
    # 1. 장면별 클린 클립 생성
    clip_paths = build_scene_clips(script, job_dir)
    durations = [scene.duration for scene in script.scenes]

    # 2. 클립 연결 + 페이드 전환
    video_only = job_dir / "video_only.mp4"
    _concat_clips_with_fade(clip_paths, durations, video_only)

    # 3. 오디오 + 자막 합성
    audio_path = audio_dir / "full_narration.mp3"
    font_path = _find_font_path()
    final_path = job_dir / (output_filename or build_video_filename(script.title))

    _add_audio_and_subtitles(video_only, audio_path, script, final_path, font_path)

    # 임시 파일 정리
    video_only.unlink(missing_ok=True)

    return final_path
