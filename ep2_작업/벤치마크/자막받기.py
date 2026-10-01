# 목록 파일에 적힌 영상 자막(한국어 자동 자막 포함)을 받아 영상마다 txt로 저장한다.
# 클라우드 서버에서는 YouTube가 막으므로, 사용자 컴퓨터에서 실행한다.
# 준비: pip install youtube-transcript-api
# 실행: 이 폴더에서  python 자막받기.py 목록파일.json   (목록파일을 안 적으면 안원잘부_영상목록.json)
import json, os, sys, time
from youtube_transcript_api import YouTubeTranscriptApi

here = os.path.dirname(os.path.abspath(__file__))
list_name = sys.argv[1] if len(sys.argv) > 1 else "안원잘부_영상목록.json"
data = json.load(open(os.path.join(here, list_name), encoding="utf-8"))
out_dir = os.path.join(here, "자막_" + list_name.replace("_영상목록.json", "").replace(".json", ""))
os.makedirs(out_dir, exist_ok=True)
api = YouTubeTranscriptApi()

for v in data["videos"]:
    path = os.path.join(out_dir, f"{v['id']}.txt")
    if os.path.exists(path):
        continue
    try:
        tr = api.fetch(v["id"], languages=["ko", "ja", "en"])
        lines = [f"[{int(s.start)//60:02d}:{int(s.start)%60:02d}] {s.text}" for s in tr.snippets]
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {v['title']} | 조회수 {v['views']} | {v['when']} | https://youtu.be/{v['id']}\n")
            f.write("\n".join(lines))
        print("받음:", v["title"])
    except Exception as e:
        print("실패:", v["title"], type(e).__name__)
    time.sleep(2)
