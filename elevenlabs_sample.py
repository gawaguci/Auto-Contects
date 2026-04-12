"""ElevenLabs 젊은 남성 한국어 음성 샘플 생성."""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

if not API_KEY:
    print("오류: .env 파일에 ELEVENLABS_API_KEY가 없습니다.")
    exit(1)

TEXT = "여섯 시간을 수영해서 탈북한 남자가 있었습니다. 온몸이 떨렸지만, 그의 머릿속엔 오직 하나뿐이었어요. 살아야 한다."

OUT = Path(r"C:\Users\gawag\OneDrive\바탕 화면\심리학\elevenlabs_samples")
OUT.mkdir(parents=True, exist_ok=True)

VOICES = [
    ("01_June_스토리텔링",     "3MTvEr8xCMCC2mL9ujrI"),
    ("02_taemin_20대자연스러움", "Ir7oQcBXWiq4oFGROCfj"),
    ("03_Taehyung_소셜미디어",  "m3gJBS8OofDJfycyA2Ip"),
    ("04_Minjoon_지적인느낌",   "nbrxrAz3eYm9NgojrmFK"),
    ("05_Chris_밝고젊은",       "PDoCXqBQFGsvfO0hNkEs"),
]

def generate(label, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": TEXT,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.5,
            "use_speaker_boost": True,
        },
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 200:
        out = OUT / f"{label}.mp3"
        out.write_bytes(resp.content)
        print(f"  [OK] {label}.mp3")
    else:
        print(f"  [FAIL] {label}: {resp.status_code} {resp.text[:100]}")

print(f"출력 폴더: {OUT}")
print(f"샘플 텍스트: {TEXT}")
print()
for label, vid in VOICES:
    generate(label, vid)

print()
print("완료! 폴더에서 mp3 파일을 열어 비교하세요.")
print(f"경로: {OUT}")
