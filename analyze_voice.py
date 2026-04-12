"""원본 음성 분석 — 피치/템포/특성 추출."""
import subprocess
import json
from pathlib import Path

MP3 = Path(r"C:\Users\gawag\OneDrive\바탕 화면\심리학\20260412-1\여섯시간을 수영해 탈북한 남자의 첫 식사_audio.mp3")

# 1. 기본 정보 (mutagen)
try:
    from mutagen.mp3 import MP3 as MutagenMP3
    from mutagen.id3 import ID3
    audio = MutagenMP3(str(MP3))
    print(f"[기본 정보]")
    print(f"  재생시간: {audio.info.length:.1f}초 ({audio.info.length/60:.1f}분)")
    print(f"  비트레이트: {audio.info.bitrate} bps")
    print(f"  샘플레이트: {audio.info.sample_rate} Hz")
    try:
        tags = ID3(str(MP3))
        for k in ['TIT2','TPE1','TCON','TENC','TSSE']:
            if k in tags:
                print(f"  {k}: {tags[k]}")
    except:
        print("  ID3 태그 없음")
except Exception as e:
    print(f"mutagen 오류: {e}")

# 2. ffprobe로 상세 분석
print()
print("[ffprobe 분석]")
try:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", str(MP3)],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        print(f"  포맷: {fmt.get('format_name')}")
        print(f"  태그: {fmt.get('tags', {})}")
        for s in data.get("streams", []):
            print(f"  코덱: {s.get('codec_name')} / 채널: {s.get('channels')} / 샘플레이트: {s.get('sample_rate')}")
    else:
        print(f"  ffprobe 오류: {result.stderr[:200]}")
except FileNotFoundError:
    print("  ffprobe 없음 (ffmpeg 미설치)")

print()
print("분석 완료.")
