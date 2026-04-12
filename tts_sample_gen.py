"""edge-tts 음성 샘플 생성 — 원본 음성과 비교용."""
import asyncio
import edge_tts
from pathlib import Path

TEXT = "200명짜리 회사가 일본 20년 독점에 칼을 꽂았다. 아무도 몰랐던 이 기업이 어떻게 일본의 아성을 무너뜨렸는지, 지금부터 알려드리겠습니다."

OUT = Path(r"C:\Users\gawag\OneDrive\바탕 화면\심리학\tts_samples")
OUT.mkdir(parents=True, exist_ok=True)

# (번호, 음성, 속도, 피치, 설명)
VOICES = [
    (1,  "ko-KR-InJoonNeural",             "+0%",  "+0Hz",  "InJoon_기본"),
    (2,  "ko-KR-InJoonNeural",             "+5%",  "+0Hz",  "InJoon_빠름"),
    (3,  "ko-KR-InJoonNeural",             "+10%", "+0Hz",  "InJoon_더빠름"),
    (4,  "ko-KR-InJoonNeural",             "+0%",  "-5Hz",  "InJoon_낮은톤"),
    (5,  "ko-KR-InJoonNeural",             "+5%",  "-5Hz",  "InJoon_빠름+낮은톤"),
    (6,  "ko-KR-InJoonNeural",             "+10%", "-10Hz", "InJoon_더빠름+낮은톤"),
    (7,  "ko-KR-HyunsuMultilingualNeural", "+0%",  "+0Hz",  "Hyunsu_기본"),
    (8,  "ko-KR-HyunsuMultilingualNeural", "+5%",  "+0Hz",  "Hyunsu_빠름"),
    (9,  "ko-KR-HyunsuMultilingualNeural", "+10%", "+0Hz",  "Hyunsu_더빠름"),
    (10, "ko-KR-HyunsuMultilingualNeural", "+0%",  "-5Hz",  "Hyunsu_낮은톤"),
]

async def generate(idx, voice, rate, pitch, label):
    fname = OUT / f"{idx:02d}_{label}.mp3"
    comm = edge_tts.Communicate(TEXT, voice, rate=rate, pitch=pitch)
    await comm.save(str(fname))
    print(f"  [{idx:02d}] {label} -> {fname.name}")

async def main():
    print(f"출력 폴더: {OUT}")
    print(f"샘플 텍스트: {TEXT}")
    print()
    for item in VOICES:
        await generate(*item)
    print()
    print("완료! 위 폴더에서 mp3 파일을 열어 원본과 비교하세요.")

if __name__ == "__main__":
    asyncio.run(main())
