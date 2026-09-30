# 유튜브(yt)·구글(web) 자동완성을 "검색어 + 가~하"로 모은다. 자동완성은 많이 찾는 순서에 가깝다.
# 사용: python3 수요_자동완성.py "일본 " "일본인 "
import json,subprocess,urllib.parse,time,sys
def ac(q,ds="yt"):
    u="https://suggestqueries.google.com/complete/search?client=firefox&hl=ko&gl=kr"+("&ds=yt" if ds=="yt" else "")+"&q="+urllib.parse.quote(q)
    r=subprocess.run(["curl","-sS","--max-time","20",u],capture_output=True).stdout
    try: return json.loads(r.decode("utf-8","ignore"))[1]
    except Exception: return []
syll="가나다라마바사아자차카타파하"
res={}
for base in sys.argv[1:]:
    for ds in ["yt","web"]:
        seen=[]
        for s in [""]+list(syll):
            for x in ac(base+s,ds):
                if x not in seen: seen.append(x)
            time.sleep(0.3)
        res[f"{ds}:{base}"]=seen
        print(f"\n### [{ds}] '{base}' 자동완성 {len(seen)}개")
        print(" | ".join(seen))
json.dump(res,open("수요_자동완성.json","w"),ensure_ascii=False,indent=0)
