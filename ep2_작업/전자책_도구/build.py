import sys, re, html, os
from split_ruby import split
from kana2hangul import reading, convert
src = sys.argv[1]; outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
SMALL = set('ゃゅょぁぃぅぇぉゎャュョァィゥェォヮっッんン')
KANA = lambda c: '\u3040' <= c <= '\u30ff'
def jp(s):
    # 1) 조각 나누기: (화면에 낼 html, 읽는 가나, 괄호 밖 글자인가)
    ents = []; i = 0
    for m in re.finditer(r'\{([^|{}]+)\|([^{}]+)\}', s):
        for ch in s[i:m.start()]: ents.append([html.escape(ch), ch, True])
        w, r = m.group(1), m.group(2)
        parts = split(w, r) if len(w) > 1 else [r]
        if parts:
            for c, pr in zip(w, parts): ents.append([f'<ruby class="r">{html.escape(c)}<rt>{html.escape(pr)}</rt></ruby>', pr, False])
        else:
            ents.append([f'<ruby class="r">{html.escape(w)}<rt>{html.escape(r)}</rt></ruby>', r, False])
        i = m.end()
    for ch in s[i:]: ents.append([html.escape(ch), ch, True])
    # 2) 조사 は·へ → わ·え (괄호 밖 글자, 덩어리 끝이나 가나가 아닌 글자 앞)
    for idx, e in enumerate(ents):
        if not e[2] or e[1] not in 'はへ' or idx == 0: continue
        prev = ents[idx - 1]
        if prev[2] and not KANA(prev[1]): continue
        nxt = next((x[1] for x in ents[idx + 1:] if x[1].strip()), '')
        if e[1] == 'は' and (not nxt or not KANA(nxt[0])): e[1] = 'わ'
        if e[1] == 'へ' and (not nxt or not KANA(nxt[0]) or nxt in 'とのは'): e[1] = 'え'
    # 3) 한글 한 덩어리로 묶기: 작은 가나·っ·ん은 앞 글자에 붙인다
    units = []
    for h, k, outside in ents:
        isk = (not outside) or KANA(k[0])
        if outside and k in SMALL and units and units[-1][2] and units[-1][1][-1:] not in 'ー':
            units[-1][0] += h; units[-1][1] += k
        else:
            units.append([h, k if isk else '', isk])
    out = []
    for h, k, isk in units:
        y = convert(k) if isk else ''
        out.append(f'<ruby class="o">{h}<rt class="o">{html.escape(y)}</rt></ruby>' if y else h)
    return ''.join(out)
title = ''; pages = []; cur = None
for raw in open(src, encoding='utf-8'):
    line = raw.rstrip('\n')
    if line.startswith('@'): title = line[1:].strip(); continue
    if line.startswith('#'):
        cur = {'name': line[1:].strip(), 'items': []}; pages.append(cur); continue
    if cur is None: continue
    if not line.strip(): cur['items'].append('<div class="gap"></div>'); continue
    cls = 'p'
    if line.startswith('*'): cls = 'p h'; line = line[1:].strip()
    if line.startswith('~'): cls = 'p note'; line = line[1:].strip()
    segs = []
    for seg in line.split(' / '):
        j, _, k = seg.partition('=')
        segs.append(f'<span class="s"><span class="j">{jp(j)}</span><span class="k">{html.escape(k)}</span></span>')
    cur['items'].append(f'<div class="{cls}">{"".join(segs)}</div>')
secs = ''.join(f'<section><div class="hd">{html.escape(title.split(" ")[0].split("_",1)[-1].replace("_"," "))} · {html.escape(p["name"])}</div><div class="text">{"".join(p["items"])}</div><div class="ft"><span>오른쪽 줄부터 왼쪽으로 · 한 줄은 위에서 아래로</span><span><b style="color:#d0021b">빨강 읽는 법</b> · <b style="color:#e07000">주황 한글 소리</b> · <b style="color:#1a8a3a">초록 뜻</b></span></div></section>' for p in pages)
doc = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Noto+Sans+KR:wght@400;500&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;background:#fff}}
section{{display:inline-block;box-sizing:border-box;padding:58px 50px 62px;position:relative;height:1240px;vertical-align:top;min-width:600px}}
.hd{{position:absolute;top:18px;right:50px;font:600 15px "Noto Sans KR",sans-serif;color:#555}}
.text{{writing-mode:vertical-rl;height:1110px;font-family:"Noto Sans JP","IPAGothic",sans-serif}}
.p{{margin-left:16px}}
.gap{{width:20px}}
.s{{display:inline-block;writing-mode:vertical-rl;vertical-align:top;margin-bottom:4px}}
.j{{display:block;font-size:22px;line-height:1.0;color:#111;font-weight:500;padding-right:13px}}
.h .j{{font-size:26px;font-weight:700}}
.y{{display:block;font-size:11.5px;line-height:1.1;color:#e07000;font-family:"Noto Sans KR","WenQuanYi Zen Hei",sans-serif;margin-left:2px;margin-top:2px}}
.k{{display:block;font-size:12.5px;line-height:1.15;color:#1a8a3a;font-family:"Noto Sans KR","WenQuanYi Zen Hei",sans-serif;margin-left:7px;margin-top:2px}}
ruby.r{{ruby-position:over}}
ruby.o{{ruby-position:under}}
rt{{font-size:10.5px;color:#d0021b;font-weight:400;padding-inline:2px}}
rt.o{{padding-inline:4px;font-size:11.5px;color:#e07000;font-family:"Noto Sans KR","WenQuanYi Zen Hei",sans-serif}}
.ft{{position:absolute;bottom:22px;left:50px;right:50px;font:12.5px "Noto Sans KR",sans-serif;color:#666;display:flex;justify-content:space-between;gap:24px}}
</style></head><body>{secs}</body></html>'''
open(f'{outdir}/{title.split(" ")[0]}.html', 'w', encoding='utf-8').write(doc)
print(f'{outdir}/{title.split(" ")[0]}.html', len(pages))
