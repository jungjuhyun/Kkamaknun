# 유튜브 검색 결과 상위 20개를 받아, 1년 안에 올라온 영상 수(공급)와 조회수 상위 6개(수요)를 본다.
# 조회수 상위 4개는 채널 이름으로 채널 검색을 해서 구독자 수를 찾는다. 다른 채널과 섞일 수 있다.
# 사용: python3 수요_유튜브.py "검색어1" "검색어2" ...
import json,re,sys,subprocess,time,urllib.parse,os
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

cache=json.load(open("수요_구독자.json")) if os.path.exists("수요_구독자.json") else {}
def subs(ch):
    if ch in cache: return cache[ch]
    time.sleep(1.5)
    url="https://www.youtube.com/results?search_query="+urllib.parse.quote(ch)+"&sp=EgIQAg%253D%253D&hl=ko&gl=KR"
    html=subprocess.run(["curl","-sS","--max-time","30","-H","Accept-Language: ko-KR",url],capture_output=True,text=True).stdout
    s="?"
    for m in re.finditer(r'"channelRenderer":\{"channelId":"[^"]+","title":\{"simpleText":"([^"]*)"\}.*?"videoCountText":\{"accessibility":\{"accessibilityData":\{"label":"([^"]*)"',html):
        if m.group(1).strip()==ch.strip():
            s=m.group(2).replace("구독자 ","").replace("명",""); break
    cache[ch]=s; json.dump(cache,open("수요_구독자.json","w"),ensure_ascii=False)
    return s
def recent(pt): return bool(re.search(r"(일|주|시간|분|개월) 전",pt)) and not re.search(r"1[2-9]개월",pt)
out=json.load(open("수요_유튜브.json")) if __import__("os").path.exists("수요_유튜브.json") else {}
def recent(pt): return bool(re.search(r"(일|주|시간|분|개월) 전",pt)) and not re.search(r"1[2-9]개월",pt)
for q in sys.argv[1:]:
    time.sleep(1.5)
    r=search(q)[:20]
    rc=sum(recent(x[3]) for x in r)
    rs=sorted(r,key=lambda x:-num(x[2]))
    print(f"\n### {q}  상위 {len(r)}개 중 1년 안에 올라온 것 {rc}개")
    rows=[]
    for i,(t,ch,vc,pt,ln,vid) in enumerate(rs[:6]):
        s=subs(ch) if i<4 else "-"
        print(f"{num(vc):>10,} | 구독 {s} | {pt} | {ln} | {ch} | {t[:55]}")
        rows.append(dict(views=num(vc),subs=s,when=pt,len=ln,ch=ch,title=t))
    out[q]=dict(n=len(r),recent=rc,rows=rows); json.dump(out,open("수요_유튜브.json","w"),ensure_ascii=False,indent=0)
