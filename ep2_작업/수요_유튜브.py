# 유튜브 검색 결과 상위 15개를 조회수 순으로 뽑고, 상위 4개 채널의 구독자 수를 채널 검색으로 찾는다.
# 사용: python3 수요_유튜브.py "검색어1" "검색어2" ...
import json,re,sys,urllib.parse,subprocess
def search(q):
    url="https://www.youtube.com/results?search_query="+urllib.parse.quote(q)+"&hl=ko&gl=KR"
    html=subprocess.run(["curl","-sS","--max-time","30","-H","Accept-Language: ko-KR","-b","CONSENT=YES+","--",url],capture_output=True,text=True).stdout
    m=re.search(r"var ytInitialData = (\{.*?\});</script>",html)
    if not m: return []
    d=json.loads(m.group(1))
    out=[]
    def walk(o):
        if isinstance(o,dict):
            if "videoRenderer" in o:
                v=o["videoRenderer"]
                t="".join(r.get("text","") for r in v.get("title",{}).get("runs",[]))
                vc=v.get("viewCountText",{}).get("simpleText") or "".join(r.get("text","") for r in v.get("viewCountText",{}).get("runs",[]))
                pt=v.get("publishedTimeText",{}).get("simpleText","")
                ch="".join(r.get("text","") for r in v.get("ownerText",{}).get("runs",[]))
                ln=v.get("lengthText",{}).get("simpleText","")
                out.append((t,ch,vc,pt,ln,v.get("videoId")))
                return
            for x in o.values(): walk(x)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d)
    return out
def num(s):
    s=s.replace(",","").replace("조회수","").replace("회","").strip()
    m=re.match(r"([\d.]+)\s*(만|천|억)?",s)
    if not m: return 0
    n=float(m.group(1)); u=m.group(2)
    return int(n*{"만":1e4,"천":1e3,"억":1e8,None:1}[u])
import json,re,sys,subprocess,time,urllib.parse,os
cache=json.load(open("subs.json")) if os.path.exists("subs.json") else {}
def subs(ch):
    if ch in cache: return cache[ch]
    time.sleep(1.5)
    url="https://www.youtube.com/results?search_query="+urllib.parse.quote(ch)+"&sp=EgIQAg%253D%253D&hl=ko&gl=KR"
    html=subprocess.run(["curl","-sS","--max-time","30","-H","Accept-Language: ko-KR",url],capture_output=True,text=True).stdout
    s="?"
    for m in re.finditer(r'"channelRenderer":\{"channelId":"[^"]+","title":\{"simpleText":"([^"]*)"\}.*?"videoCountText":\{"accessibility":\{"accessibilityData":\{"label":"([^"]*)"',html):
        if m.group(1).strip()==ch.strip():
            s=m.group(2).replace("구독자 ","").replace("명",""); break
    cache[ch]=s; json.dump(cache,open("subs.json","w"),ensure_ascii=False)
    return s
out=json.load(open("all.json")) if os.path.exists("all.json") else {}
for q in sys.argv[1:]:
    time.sleep(1.5)
    r=sorted(search(q)[:15],key=lambda x:-num(x[2]))
    print(f"\n### {q}  (상위 {len(r)}개, 조회수 순 6개)")
    rows=[]
    for i,(t,ch,vc,pt,ln,vid) in enumerate(r[:6]):
        s=subs(ch) if i<4 else "-"
        print(f"{num(vc):>10,} | 구독 {s} | {pt} | {ln} | {ch} | {t[:55]}")
        rows.append(dict(views=num(vc),subs=s,when=pt,len=ln,ch=ch,title=t,id=vid))
    out[q]=rows; json.dump(out,open("all.json","w"),ensure_ascii=False,indent=0)
