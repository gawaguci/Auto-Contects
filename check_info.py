import json
p = r"C:\Users\gawag\OneDrive\바탕 화면\심리학\20260412-1\여섯시간을 수영해 탈북한 남자의 첫 식사_audio.info.json"
with open(p, encoding="utf-8") as f:
    d = json.load(f)
for k in ["uploader","uploader_id","uploader_url","channel","channel_id","webpage_url","id","title"]:
    print(f"{k}: {d.get(k,'')}")
