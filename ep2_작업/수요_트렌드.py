# 구글 트렌드(한국, 최근 12개월) 웹 검색과 유튜브 검색의 상대 검색량. pip install pytrends 필요.
import time,sys
from pytrends.request import TrendReq
p=TrendReq(hl='ko-KR',tz=-540)
groups=[["니지모리","애니 음식","에호마키","아덕페","애니 팝업"],["니지모리","AGF","내한 공연","일본 편의점","애니 성지"]]
for gp in ["","youtube"]:
    for g in groups:
        for t in range(3):
            try:
                p.build_payload(g,geo='KR',timeframe='today 12-m',gprop=gp)
                df=p.interest_over_time()
                print(f"\n[{gp or 'web'}] 12개월 평균 / 최고 / 최고 주",flush=True)
                for k in g:
                    s=df[k]; print(f"  {k:10s} 평균 {s.mean():6.1f}  최고 {s.max():4d}  {s.idxmax().date()}",flush=True)
                break
            except Exception as e: print("ERR",g,gp,e,flush=True); time.sleep(20)
        time.sleep(8)
