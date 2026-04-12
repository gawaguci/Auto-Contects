"""Remotion 렌더링 브릿지.

Script → JSON → npx remotion render → 주제 기반 mp4
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import config
from pipeline.file_naming import build_video_filename
from pipeline.image_gen import generate_scene_image
from pipeline.script_gen import Script
from pipeline.stock_image import fetch_bg_images_for_script

_HEADLESS_SHELLS = [
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
    "/opt/pw-browsers/chromium_headless_shell/chrome-linux/headless_shell",
]


def _browser() -> str | None:
    p = os.environ.get("REMOTION_BROWSER_EXECUTABLE")
    if p and Path(p).is_file():
        return p
    return next((p for p in _HEADLESS_SHELLS if Path(p).is_file()), None)


def _cmd(name: str) -> str:
    """Windows에서 npm/npx는 .cmd 확장자 필요."""
    if os.name == "nt":
        found = shutil.which(f"{name}.cmd") or shutil.which(name)
        return found or name
    return shutil.which(name) or name


def _check_deps() -> None:
    if not shutil.which("node"):
        raise RuntimeError("Node.js가 설치되어 있지 않습니다.")
    nm = config.REMOTION_DIR / "node_modules"
    if nm.is_dir():
        return
    print("    npm install (최초 1회)...")
    r = subprocess.run(
        [_cmd("npm"), "install"], cwd=str(config.REMOTION_DIR),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError(f"npm install 실패:\n{(r.stderr or '')[-1500:]}")


def _remotion_cli_cmd() -> list[str]:
    """Remotion CLI 실행 커맨드 (npx 인자 누락 이슈 회피)."""
    node_bin = shutil.which("node")
    if not node_bin:
        raise RuntimeError("Node.js 실행 파일(node)을 찾을 수 없습니다.")

    cli_js = config.REMOTION_DIR / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
    if not cli_js.exists():
        raise RuntimeError(f"Remotion CLI 파일이 없습니다: {cli_js}")

    return [node_bin, str(cli_js)]


def _copy_audio_to_public(job_dir: Path) -> tuple[Path, str]:
    """오디오를 remotion/public/에 복사하고 staticFile 경로(상대) 반환."""
    job_id = job_dir.name
    pub_audio = config.REMOTION_DIR / "public" / "audio" / job_id
    pub_audio.mkdir(parents=True, exist_ok=True)

    src = job_dir / "audio"
    # full_narration + 씬별 파일 모두 복사
    for mp3 in src.glob("*.mp3"):
        shutil.copy2(mp3, pub_audio / mp3.name)

    full_static = f"audio/{job_id}/full_narration.mp3"  # staticFile() 상대경로
    return pub_audio, full_static


def _parse_srt(srt_path: Path) -> list[dict]:
    """SRT 파일 파싱 → [{start, end, text}, ...] 리스트 반환."""
    if not srt_path.exists():
        return []
    entries = []
    text = srt_path.read_text(encoding="utf-8-sig")
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        # lines[0]: 번호, lines[1]: 타임코드, lines[2+]: 텍스트
        try:
            ts = lines[1]
            parts = ts.split(" --> ")
            def _srt_to_sec(t: str) -> float:
                t = t.replace(",", ".")
                h, m, rest = t.split(":")
                s, ms = rest.split(".")
                return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
            start = _srt_to_sec(parts[0].strip())
            end = _srt_to_sec(parts[1].strip())
            sub_text = " ".join(lines[2:]).strip()
            entries.append({"start": start, "end": end, "text": sub_text})
        except Exception:
            continue
    return entries


def prepare_scene_images(
    script: Script,
    category: dict,
    job_dir: Path,
    image_style: int = 0,
) -> dict[int, Path]:
    """스크립트의 씬 이미지를 job_dir/images에 준비해 반환."""
    scene_dicts = [
        {
            "index": s.index,
            "video_query": s.video_query,
            "image_prompt": s.image_prompt,
            "narration": s.narration,
        }
        for s in script.scenes
    ]

    bg_images: dict[int, str] = {}
    _img_keys = ("GEMINI_API_KEY", "PEXELS_API_KEY", "PIXABAY_API_KEY")
    if any(os.environ.get(k) for k in _img_keys):
        provider = "Gemini" if os.environ.get("GEMINI_API_KEY") else "스톡"
        print(f"    배경 이미지 생성 중 ({provider})...")
        bg_images = fetch_bg_images_for_script(
            scene_dicts,
            delay=1.0,
            title=script.title,
            category=script.category,
            image_style=image_style,
        )
        print(f"    배경 이미지 {len(bg_images)}/{len(scene_dicts)}개 완료")
    else:
        print("    이미지 API 키 없음 - 기본 장면 이미지로 대체합니다.")

    images_dir = job_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    total_scenes = len(script.scenes)
    fallback_count = 0
    copied_count = 0
    scene_images: dict[int, Path] = {}
    for scene in script.scenes:
        idx = scene.index
        current = bg_images.get(idx, "")
        if current and Path(current).exists():
            src = Path(current)
            ext = src.suffix.lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                ext = ".png"
            dst = images_dir / f"scene_{idx:02d}{ext}"
            if not dst.exists() or dst.stat().st_size <= 0:
                shutil.copy2(src, dst)
            scene_images[idx] = dst
            copied_count += 1
            continue

        fallback = images_dir / f"scene_{idx:02d}.png"
        if not fallback.exists() or fallback.stat().st_size <= 0:
            generate_scene_image(
                scene_index=idx,
                total_scenes=total_scenes,
                subtitle=scene.subtitle,
                bg_color=scene.bg_color,
                title=script.title,
                emoji=category.get("emoji", "🎬"),
                output_path=fallback,
                image_style=image_style,
            )
        scene_images[idx] = fallback
        fallback_count += 1

    if copied_count > 0:
        print(f"    외부 이미지 적용 {copied_count}/{total_scenes}개")
    if fallback_count > 0:
        print(f"    기본 이미지 폴백 {fallback_count}/{total_scenes}개 적용")

    return scene_images


def _to_json(script: Script, category: dict, job_dir: Path, image_style: int = 0) -> Path:
    audio = job_dir / "audio"

    full = audio / "full_narration.mp3"
    if not full.exists():
        raise FileNotFoundError(f"오디오 없음: {full}")

    # Remotion은 public/ 폴더 파일만 staticFile()로 참조 가능
    pub_audio, full_static = _copy_audio_to_public(job_dir)
    job_id = job_dir.name

    scene_images = prepare_scene_images(script, category, job_dir, image_style=image_style)

    # bgImage를 remotion/public/images/{job_id}/ 에 복사 → staticFile 경로로
    pub_images = config.REMOTION_DIR / "public" / "images" / job_id
    def _copy_bg(local_path: str, scene_idx: int) -> str:
        if not local_path:
            return ""
        src = Path(local_path)
        if not src.exists():
            return ""
        pub_images.mkdir(parents=True, exist_ok=True)
        ext = src.suffix or ".png"
        dst = pub_images / f"scene_{scene_idx:02d}{ext}"
        shutil.copy2(src, dst)
        return f"images/{job_id}/scene_{scene_idx:02d}{ext}"

    # SRT 자막 파싱 → subtitles 배열
    subtitles = _parse_srt(job_dir / "subtitles.srt")

    data = {
        "version": script.version,
        "title": script.title,
        "category": script.category,
        "categoryEmoji": category.get("emoji", ""),
        "categoryId": category.get("id"),
        "totalDuration": script.total_duration,
        "cta": script.cta,
        "fps": config.VIDEO_CONFIG["fps"],
        "width": config.VIDEO_CONFIG["width"],
        "height": config.VIDEO_CONFIG["height"],
        "fullAudioFile": full_static,
        "scenes": [
            {
                "index": s.index,
                "duration": s.duration,
                "narration": s.narration,
                "subtitle": s.subtitle,
                "imagePrompt": s.image_prompt,
                "bgColor": s.bg_color,
                "bgImage": _copy_bg(str(scene_images.get(s.index, "")), s.index),
                "audioFile": f"audio/{job_id}/scene_{s.index:02d}.mp3",
            }
            for s in script.scenes
        ],
        "subtitles": subtitles,
    }

    out = job_dir / "remotion_input.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def render_video(
    script: Script,
    category: dict,
    job_dir: Path,
    version: str = "shorts",
    concurrency: int = 4,
    output_filename: str | None = None,
    image_style: int = 0,
) -> Path:
    """Remotion으로 영상 자동 렌더링."""
    _check_deps()
    props = _to_json(script, category, job_dir, image_style=image_style)
    out = job_dir / (output_filename or build_video_filename(script.title))

    cmd = [
        *_remotion_cli_cmd(), "render",
        "src/index.ts", "VideoComposition", str(out),
        f"--props={props}",
        "--codec=h264",
        f"--concurrency={concurrency}",
    ]
    browser = _browser()
    if browser:
        cmd.append(f"--browser-executable={browser}")

    n = len(script.scenes)
    print(f"    렌더링 시작 ({script.total_duration:.1f}초, {n}씬)...")

    try:
        r = subprocess.run(
            cmd, cwd=str(config.REMOTION_DIR),
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("렌더링 타임아웃 (30분)")

    if r.returncode != 0:
        raise RuntimeError(f"렌더링 실패:\n{(r.stderr or '')[-1500:]}")
    if not out.exists():
        raise RuntimeError(f"출력 파일 없음: {out}")

    mb = out.stat().st_size / 1024 / 1024
    print(f"    완료 ({mb:.1f}MB)")
    return out


def open_studio(
    script: Script,
    category: dict,
    job_dir: Path,
    output_filename: str | None = None,
    image_style: int = 0,
) -> Path:
    """Remotion Studio를 열어 수동 렌더링 대기. remotion_input.json 경로 반환.

    --props에 Windows 절대경로를 전달하면 Remotion Studio가 JSON으로 파싱을 시도해
    SyntaxError가 발생한다. props 파일을 remotion/ 디렉토리에 복사해 상대경로로 전달.
    """
    _check_deps()
    props = _to_json(script, category, job_dir, image_style=image_style)

    # props를 remotion/ cwd 기준 상대경로로 전달 (Windows 절대경로 파싱 오류 방지)
    studio_props = config.REMOTION_DIR / "studio_props.json"
    shutil.copy2(props, studio_props)

    cmd = [
        *_remotion_cli_cmd(), "studio",
        "src/index.ts",
        "--props=studio_props.json",
    ]

    n = len(script.scenes)
    print(f"    Remotion Studio 열기 ({script.total_duration:.1f}초, {n}씬)...")
    print()
    print("    ★ Studio에서 직접 렌더링 후 완료되면 Enter를 누르세요.")

    # Studio는 블로킹 없이 백그라운드로 실행
    subprocess.Popen(
        cmd, cwd=str(config.REMOTION_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )

    try:
        input("    Studio 렌더링 완료 후 Enter → ")
    except (EOFError, KeyboardInterrupt):
        pass

    expected_name = output_filename or build_video_filename(script.title)
    out = job_dir / expected_name
    if out.exists():
        mb = out.stat().st_size / 1024 / 1024
        print(f"    완료 ({mb:.1f}MB)")
    else:
        print(f"    ({expected_name} 미확인 — Studio에서 {job_dir} 경로로 저장했는지 확인)")

    return props
