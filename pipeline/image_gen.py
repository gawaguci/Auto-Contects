"""Pillow 기반 1080x1920 이미지 생성."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config
from pipeline.script_gen import Script

# 폰트 탐색 경로
_FONT_SEARCH_PATHS = [
    "NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic-Bold.ttf",
    "C:\\Windows\\Fonts\\NanumGothicBold.ttf",
    "C:\\Windows\\Fonts\\malgunbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

# 폰트 캐시
_font_cache: dict[int, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}

_STYLE_TINTS: dict[int, tuple[int, int, int]] = {
    1: (30, 30, 35),      # 시네마틱
    2: (120, 155, 180),   # 수채화
    3: (255, 170, 60),    # 카툰
    4: (255, 95, 180),    # 애니메이션
    5: (170, 120, 70),    # 유화
    6: (160, 160, 160),   # 연필 스케치
    7: (235, 235, 235),   # 흰 얼굴 캐릭터
}


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """폰트 탐색 후 캐시."""
    if size in _font_cache:
        return _font_cache[size]

    for path in _FONT_SEARCH_PATHS:
        try:
            font = ImageFont.truetype(path, size)
            _font_cache[size] = font
            return font
        except (OSError, IOError):
            continue

    font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """hex 색상을 RGB 튜플로 변환."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        hex_color = "1a1a2e"
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _darken_color(rgb: tuple[int, int, int], factor: float = 0.4) -> tuple[int, int, int]:
    """색상을 어둡게."""
    return tuple(int(c * factor) for c in rgb)


def _mix_color(base: tuple[int, int, int], tint: tuple[int, int, int], ratio: float = 0.35) -> tuple[int, int, int]:
    """base와 tint를 ratio 비율로 혼합."""
    r = int(base[0] * (1 - ratio) + tint[0] * ratio)
    g = int(base[1] * (1 - ratio) + tint[1] * ratio)
    b = int(base[2] * (1 - ratio) + tint[2] * ratio)
    return r, g, b


def _draw_gradient(draw: ImageDraw.Draw, width: int, height: int,
                   top_color: tuple, bottom_color: tuple) -> None:
    """상하 그라디언트 배경 그리기."""
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """텍스트를 max_width에 맞게 줄바꿈."""
    if not text:
        return [""]

    lines = []
    current = ""
    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines or [""]


def _fit_single_line_text(
    text: str,
    draw: ImageDraw.Draw,
    max_width: int,
    base_size: int = 100,
    min_size: int = 54,
) -> tuple[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    """텍스트를 한 줄로 맞추기 위해 폰트 크기/문자열을 조정."""
    text = (text or "").strip()
    if not text:
        return "", _find_font(min_size)

    for size in range(base_size, min_size - 1, -2):
        font = _find_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return text, font

    # 최소 폰트에서도 초과하면 말줄임 처리
    font = _find_font(min_size)
    ellipsis = "..."
    trimmed = text
    while len(trimmed) > 1:
        candidate = trimmed + ellipsis
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return candidate, font
        trimmed = trimmed[:-1]

    return ellipsis, font


def _draw_text_with_shadow(
    draw: ImageDraw.Draw,
    pos: tuple[int, int],
    text: str,
    font,
    fill: tuple = (255, 255, 255),
    shadow_offset: int = 3,
) -> None:
    """그림자 효과 텍스트."""
    x, y = pos
    # 그림자
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 180))
    # 본문
    draw.text((x, y), text, font=font, fill=fill)


def generate_scene_image(
    scene_index: int,
    total_scenes: int,
    subtitle: str,
    bg_color: str,
    title: str,
    emoji: str,
    output_path: Path,
    image_style: int = 0,
) -> Path:
    """한 장면의 이미지 생성."""
    width = config.VIDEO_CONFIG["width"]
    height = config.VIDEO_CONFIG["height"]

    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 1. 그라디언트 배경
    top_rgb = _hex_to_rgb(bg_color)
    tint = _STYLE_TINTS.get(image_style)
    if tint:
        top_rgb = _mix_color(top_rgb, tint, ratio=0.35)
    bottom_rgb = _darken_color(top_rgb, 0.4)
    _draw_gradient(draw, width, height, top_rgb, bottom_rgb)

    # 2. 상단: 이모지 + 제목
    title_font = _find_font(48)
    header_text = f"{emoji} {title}"
    wrapped_header = _wrap_text(header_text, title_font, width - 120, draw)
    y_pos = 100
    for line in wrapped_header[:2]:  # 최대 2줄
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        x_pos = (width - tw) // 2
        _draw_text_with_shadow(draw, (x_pos, y_pos), line, title_font)
        y_pos += 70

    # 3. 중앙: 대형 자막 (한 줄 고정, 길면 폰트 자동 축소)
    max_text_width = width - 160
    subtitle_text, subtitle_font = _fit_single_line_text(
        subtitle, draw, max_text_width, base_size=100, min_size=54
    )
    bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x_pos = (width - tw) // 2
    y_pos = (height - th) // 2
    _draw_text_with_shadow(draw, (x_pos, y_pos), subtitle_text, subtitle_font, shadow_offset=4)

    # RGB로 변환 후 저장 (RGBA → RGB)
    img_rgb = img.convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img_rgb.save(str(output_path), "PNG")
    return output_path


def generate_images(script: Script, category: dict, job_dir: Path, image_style: int = 0) -> list[Path]:
    """스크립트의 모든 장면 이미지 생성.

    Args:
        script: 스크립트 객체
        category: 카테고리 설정
        job_dir: output/{job_id} 경로

    Returns:
        생성된 이미지 파일 경로 리스트
    """
    images_dir = job_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    total = len(script.scenes)
    paths = []

    for scene in script.scenes:
        output_path = images_dir / f"scene_{scene.index:02d}.png"
        generate_scene_image(
            scene_index=scene.index,
            total_scenes=total,
            subtitle=scene.subtitle,
            bg_color=scene.bg_color,
            title=script.title,
            emoji=category["emoji"],
            output_path=output_path,
            image_style=image_style,
        )
        paths.append(output_path)

    return paths
