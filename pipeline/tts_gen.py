"""TTS 음성 생성 — edge-tts / ElevenLabs / Typecast 지원."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import edge_tts
import requests

import config
from pipeline.script_gen import Script

_FFMPEG_FALLBACK_DIRS = [
    Path(r"C:\\ffmpeg\\bin"),
    Path(r"C:\\ffmpeg"),
    Path(r"C:\\Program Files\\ffmpeg\\bin"),
    Path(r"C:\\Program Files (x86)\\ffmpeg\\bin"),
]


def _resolve_binary(name: str) -> str | None:
    """실행 파일 경로를 결정한다 (PATH + Windows 기본 경로)."""
    env_keys = [f"{name.upper()}_BIN"]
    if name == "ffmpeg":
        env_keys.append("FFMPEG_PATH")

    for key in env_keys:
        raw = os.environ.get(key, "").strip().strip('"')
        if not raw:
            continue
        candidate = Path(raw)
        if candidate.is_dir():
            candidate = candidate / (f"{name}.exe" if os.name == "nt" else name)
        if candidate.exists():
            return str(candidate)

    found = shutil.which(name)
    if found:
        return found

    if os.name == "nt":
        exe_name = f"{name}.exe"
        for base in _FFMPEG_FALLBACK_DIRS:
            candidate = base / exe_name
            if candidate.exists():
                return str(candidate)

    return None


_EDGE_EN_FALLBACK_VOICE_BY_CATEGORY = {
    1: "en-US-JennyNeural",
    2: "en-US-GuyNeural",
    3: "en-US-JennyNeural",
    4: "en-US-GuyNeural",
    5: "en-US-GuyNeural",
    6: "en-US-GuyNeural",
}


def _get_voice_settings(category: dict, version: str, language: str = "ko") -> tuple[str, str, str]:
    """카테고리 + 버전에 맞는 voice, rate, pitch 반환."""
    if language == "en":
        voice = (
            category.get("voice_en")
            or _EDGE_EN_FALLBACK_VOICE_BY_CATEGORY.get(category.get("id"), "en-US-JennyNeural")
        )
    else:
        voice = category["voice"]
    rate = category["shorts_rate"] if version == "shorts" else category["longform_rate"]
    pitch = category["pitch"]
    return voice, rate, pitch


# ──────────────────────────────────────────────
# edge-tts
# ──────────────────────────────────────────────

async def _generate_scene_audio(
    text: str, voice: str, rate: str, pitch: str, output_path: Path
) -> None:
    """edge-tts: 한 장면의 TTS 음성 생성."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))


# ──────────────────────────────────────────────
# ElevenLabs
# ──────────────────────────────────────────────

def _elevenlabs_generate(text: str, voice_id: str, output_path: Path) -> None:
    """ElevenLabs TTS 생성."""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY가 .env에 없습니다.")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.5,
            "use_speaker_boost": True,
        },
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs 오류 {resp.status_code}: {resp.text[:200]}")
    output_path.write_bytes(resp.content)


# ──────────────────────────────────────────────
# Typecast
# ──────────────────────────────────────────────

def _typecast_generate(
    text: str,
    voice_id: str,
    tempo: float,
    output_path: Path,
    language: str = "ko",
) -> None:
    """Typecast TTS 생성 (동기 엔드포인트)."""
    api_key = os.environ.get("TYPECAST_API_KEY", "")
    if not api_key:
        raise RuntimeError("TYPECAST_API_KEY가 .env에 없습니다.")

    url = "https://api.typecast.ai/v1/text-to-speech"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "voice_id": voice_id,
        "model": "ssfm-v30",
        "language": "eng" if language == "en" else "kor",
        "output": {
            "format": "mp3",
            "audio_tempo": tempo,
            "volume": 100,
            "audio_pitch": 0,
        },
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Typecast 오류 {resp.status_code}: {resp.text[:200]}")
    output_path.write_bytes(resp.content)


def get_audio_duration(path: Path) -> float:
    """오디오 파일 재생시간 측정 (초 단위).

    우선순위: ffprobe → mutagen → 파일크기 추정
    """
    # 1. ffprobe (ffmpeg 설치된 환경)
    ffprobe_bin = _resolve_binary("ffprobe")
    if ffprobe_bin:
        result = subprocess.run(
            [ffprobe_bin, "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return float(info["format"]["duration"])

    # 2. mutagen (ffprobe 없을 때)
    try:
        from mutagen.mp3 import MP3
        audio = MP3(str(path))
        return audio.info.length
    except Exception:
        pass

    # 3. 최후 수단: 파일 크기로 추정 (128kbps 기준)
    size_bytes = path.stat().st_size
    return size_bytes / (128 * 1024 / 8)


def _concat_audio_files(audio_files: list[Path], output_path: Path) -> None:
    """오디오 파일 연결. ffmpeg → pydub → raw 바이트 순 fallback."""
    # 1. ffmpeg
    ffmpeg_bin = _resolve_binary("ffmpeg")
    if ffmpeg_bin:
        list_file = output_path.parent / "concat_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for audio in audio_files:
                f.write(f"file '{audio.resolve()}'\n")
        result = subprocess.run(
            [ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        list_file.unlink(missing_ok=True)
        if result.returncode == 0:
            return

    # 2. pydub
    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for f in audio_files:
            combined += AudioSegment.from_mp3(str(f))
        combined.export(str(output_path), format="mp3")
        return
    except Exception:
        pass

    # 3. 가장 긴 파일을 full_narration으로 복사 (최후 수단)
    longest = max(audio_files, key=lambda p: p.stat().st_size)
    import shutil as _sh
    _sh.copy2(str(longest), str(output_path))


def generate_tts(
    script: Script,
    category: dict,
    job_dir: Path,
    provider: str = "edge-tts",
    language: str = "ko",
) -> Script:
    """스크립트 기반 TTS 음성 생성.

    Args:
        script: 스크립트 객체
        category: 카테고리 설정
        job_dir: output/{job_id} 경로
        provider: "edge-tts" | "elevenlabs" | "typecast"

    Returns:
        duration이 실제 TTS 길이로 업데이트된 Script
    """
    audio_dir = job_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    voice, rate, pitch = _get_voice_settings(category, script.version, language)

    # provider별 voice_id 결정
    if provider == "elevenlabs":
        # 카테고리에 elevenlabs_voice_id 설정이 있으면 사용, 없으면 기본값 June
        el_voice_id = category.get("elevenlabs_voice_id", "3MTvEr8xCMCC2mL9ujrI")
    elif provider == "typecast":
        tc_voice_id = category.get("typecast_voice_id") or os.environ.get("TYPECAST_VOICE_ID", "")
        if not tc_voice_id:
            print("    Typecast voice_id 미설정 - Edge-TTS로 자동 전환합니다.")
            provider = "edge-tts"
        # rate(+10% 형식)를 tempo(1.1 형식)로 변환
        rate_str = rate.replace("%", "").replace("+", "")
        tempo = round(1.0 + int(rate_str) / 100, 2) if rate_str else 1.0

    scene_audio_files: list[Path] = []

    # 장면별 TTS 생성
    for scene in script.scenes:
        audio_path = audio_dir / f"scene_{scene.index:02d}.mp3"

        if provider == "edge-tts":
            asyncio.run(
                _generate_scene_audio(scene.narration, voice, rate, pitch, audio_path)
            )
        elif provider == "elevenlabs":
            _elevenlabs_generate(scene.narration, el_voice_id, audio_path)
        elif provider == "typecast":
            _typecast_generate(scene.narration, tc_voice_id, tempo, audio_path, language=language)
        else:
            raise ValueError(f"알 수 없는 TTS provider: {provider}")

        # 실제 재생시간으로 duration 업데이트
        actual_duration = get_audio_duration(audio_path)
        scene.duration = round(actual_duration, 2)
        scene_audio_files.append(audio_path)

    # 전체 합본 생성
    full_narration = audio_dir / "full_narration.mp3"
    _concat_audio_files(scene_audio_files, full_narration)

    # total_duration 업데이트
    script.total_duration = round(sum(s.duration for s in script.scenes), 2)

    # 자막 파일 생성 (SRT + VTT)
    _generate_subtitles(script, job_dir)

    return script


def apply_playback_speed(script: Script, job_dir: Path, speed_percent: int) -> Script:
    """생성된 TTS 오디오의 재생 속도를 조정하고 duration을 재계산한다.

    Args:
        script: duration이 채워진 Script
        job_dir: output/{job_id}
        speed_percent: +30, +20, +15, +10, 0, -10, -20
    """
    if speed_percent == 0:
        return script

    ffmpeg_bin = _resolve_binary("ffmpeg")
    if not ffmpeg_bin:
        print("    ffmpeg가 없어 재생 속도 조정을 건너뜁니다.")
        return script

    speed_ratio = 1.0 + (speed_percent / 100.0)
    if speed_ratio <= 0:
        raise ValueError(f"유효하지 않은 재생 속도: {speed_percent}")

    audio_dir = job_dir / "audio"
    if not audio_dir.exists():
        raise FileNotFoundError(f"오디오 폴더가 없습니다: {audio_dir}")

    mp3_files = sorted(audio_dir.glob("*.mp3"))
    if not mp3_files:
        raise FileNotFoundError(f"속도 조정 대상 mp3가 없습니다: {audio_dir}")

    for src in mp3_files:
        tmp = src.with_name(f"{src.stem}.speed.tmp.mp3")
        cmd = [
            ffmpeg_bin, "-y",
            "-i", str(src),
            "-filter:a", f"atempo={speed_ratio:.4f}",
            "-vn",
            str(tmp),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or not tmp.exists():
            err = (result.stderr or "")[-300:]
            raise RuntimeError(f"재생 속도 조정 실패 ({src.name}): {err}")
        tmp.replace(src)

    for scene in script.scenes:
        scene_audio = audio_dir / f"scene_{scene.index:02d}.mp3"
        if scene_audio.exists():
            scene.duration = round(get_audio_duration(scene_audio), 2)

    script.total_duration = round(sum(s.duration for s in script.scenes), 2)
    return script


def _format_srt_time(seconds: float) -> str:
    """초를 SRT 타임코드로 변환. 예: 00:00:05,430"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_vtt_time(seconds: float) -> str:
    """초를 VTT 타임코드로 변환. 예: 00:00:05.430"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


_FADE_SEC = 0.15  # Remotion TransitionSeries 전환 오버랩 (utils.ts FADE_SEC와 동일)
_FPS = 30         # config.VIDEO_CONFIG["fps"]와 동일


def _ceil_frames(sec: float, fps: int = _FPS) -> int:
    """utils.ts frames() 와 동일 — Math.ceil(sec * fps)."""
    import math
    return math.ceil(sec * fps)


def _scene_offsets(scenes: list) -> list[tuple[float, float]]:
    """씬별 (start_sec, duration_sec) — Remotion sceneOffsets()와 프레임 단위까지 동일.

    utils.ts sceneOffsets()는 Math.ceil로 프레임 변환 후 누적하므로
    Python도 동일하게 ceil 기반으로 계산해야 오디오와 자막 싱크가 맞는다.
    """
    fade_frames = _ceil_frames(_FADE_SEC)
    result = []
    cursor_frames = 0
    for i, scene in enumerate(scenes):
        dur_frames = _ceil_frames(scene.duration)
        start_sec = cursor_frames / _FPS
        dur_sec = dur_frames / _FPS
        result.append((start_sec, dur_sec))
        if i < len(scenes) - 1:
            cursor_frames += dur_frames - fade_frames
        else:
            cursor_frames += dur_frames
    return result


def _generate_subtitles(script: "Script", job_dir: Path) -> None:
    """씬별 narration을 문장 단위로 분할해 SRT/VTT 자막 생성.

    - 자막 내용: narration을 마침표/느낌표/물음표 기준으로 문장 분할 후 순차 표시.
      각 문장에 씬 duration을 균등 배분 → TTS 음성과 자연스럽게 싱크.
    - 타이밍: Remotion sceneOffsets()와 프레임 단위까지 동일 (ceil 기반 누적).
    """
    import re
    offsets = _scene_offsets(script.scenes)
    srt_lines = []
    vtt_lines = ["WEBVTT", ""]
    entry_idx = 1

    for scene, (scene_start, scene_dur) in zip(script.scenes, offsets):
        narration = scene.narration.strip()
        if not narration:
            continue

        # 문장 분리
        sentences = re.split(r'(?<=[.!?。！？])\s*', narration)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            sentences = [narration]

        # 각 문장에 시간 균등 배분
        dur_per = scene_dur / len(sentences)

        for j, sentence in enumerate(sentences):
            s_start = scene_start + j * dur_per
            s_end   = scene_start + (j + 1) * dur_per

            srt_lines.append(str(entry_idx))
            srt_lines.append(f"{_format_srt_time(s_start)} --> {_format_srt_time(s_end)}")
            srt_lines.append(sentence)
            srt_lines.append("")

            vtt_lines.append(f"{_format_vtt_time(s_start)} --> {_format_vtt_time(s_end)}")
            vtt_lines.append(sentence)
            vtt_lines.append("")

            entry_idx += 1

    srt_path = job_dir / "subtitles.srt"
    vtt_path = job_dir / "subtitles.vtt"

    srt_path.write_text("\n".join(srt_lines), encoding="utf-8-sig")
    vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")

    print(f"    자막: {srt_path.name} / {vtt_path.name} ({entry_idx - 1}개 항목)")
