# Perplexity Agent API(preset fast)로 질문을 보내고 답·출처·비용을 모은다. 키는 클라우드 환경 자격 증명(api.perplexity.ai, Bearer)으로 자동으로 붙는다. 코드에 키를 쓰지 않는다.
import json,subprocess,sys
SUFFIX=" 한국어로 답하라. 한국 유튜브, 네이버 블로그·카페, 디시인사이드·더쿠 같은 커뮤니티를 우선 찾는다. 영상이면 제목·채널·조회수·올린 시기를, 글이면 제목·날짜를 적는다. 모르는 것은 모른다고 쓴다. 출처 URL을 붙인다."
qs={
"q1_2편전제":"애니만 오래 봐서 일본어가 대충 들리지만, 동사 활용(て형, ない형, 가능형, 과거형)이 붙으면 못 알아듣는다는 경험담이나 영상이 한국에 있나? 사람들이 이 문제에 얼마나 공감하나?",
"q2_2편공급":"한국 유튜브에서 '애니로 일본어 공부한 뒤 자막 없이 애니 보기', '일본어 공부 전후 비교', '애니 일본어 몇 % 들리나' 같은 영상은 얼마나 있고, 최근 1년에 올라온 것은 어떤 것이 있나? 조회수가 높은 것은?",
"q3_다마고치":"다마고치를 일본어로 설정해서 키우며 일본어(히라가나·가타카나)를 배운 한국 사람의 블로그나 유튜브가 있나? 반응은 어떤가?",
"q4_게임으로일본어":"포켓몬, 동물의 숲 같은 게임을 일본어로 설정해서 일본어를 배우는 한국 유튜브 영상이나 블로그는 얼마나 있고, 조회수가 높은 것은 무엇인가?",
"q5_VR챗일본인":"한국 사람이 VR챗에서 일본인 친구를 사귄 경험담(네이버 블로그, 디시 VR챗 갤러리, 유튜브)은 최근 1년에 어떤 것이 있나? 일본어를 못 해도 됐다는 이야기가 있나?",
"q6_일본인친구수요":"한국 사람들이 '일본인 친구 사귀기'를 검색하는 이유와 가장 많이 막히는 점은 무엇인가? 네이버 지식인·블로그·커뮤니티 글 기준으로.",
}
out={}
for k,q in qs.items():
    body=json.dumps({"preset":"fast","input":q+SUFFIX},ensure_ascii=False)
    r=subprocess.run(["curl","-sS","--max-time","180","https://api.perplexity.ai/v1/agent","-H","Content-Type: application/json","-d",body],capture_output=True,text=True).stdout
    try: d=json.loads(r)
    except Exception: out[k]={"raw":r[:500]}; continue
    texts=[];urls=[]
    def walk(o):
        if isinstance(o,dict):
            for kk,v in o.items():
                if kk=='text' and isinstance(v,str): texts.append(v)
                elif kk=='url' and isinstance(v,str): urls.append(v)
                else: walk(v)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d.get('output'))
    cost=d.get('usage',{}).get('cost',{}).get('total_cost')
    out[k]={"q":q,"text":"\n".join(texts),"urls":list(dict.fromkeys(urls)),"cost":cost,"error":d.get('error')}
    print(f"\n######## {k} | cost {cost}\n"+out[k]["text"][:2500])
json.dump(out,open("res.json","w"),ensure_ascii=False,indent=1)
print("\nTOTAL", sum((v.get('cost') or 0) for v in out.values()))
