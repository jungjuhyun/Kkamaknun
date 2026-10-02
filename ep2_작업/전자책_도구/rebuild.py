import json, glob, unicodedata, re
gm = json.load(open('book/glyphmap.json'))
def pri(ch):
    o = ord(ch)
    if 0x20 <= o <= 0x7E: return 0
    if 0x3040 <= o <= 0x30FF: return 1
    if 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF: return 2
    if 0x2460 <= o <= 0x24FF: return 3
    if ch in '…・': return 3
    return 9
def fix(k):
    best, s1, sec, s2 = gm[k]
    if s1 - s2 < 0.001 and pri(sec) < pri(best): return sec
    return best
TR = lambda ch: len(ch)==1 and (0x4E00<=ord(ch)<=0x9FFF or 0x3400<=ord(ch)<=0x4DBF or 0x2E80<=ord(ch)<=0x2FDF or 0xAC00<=ord(ch)<=0xD7AF or 0x3130<=ord(ch)<=0x318F or 0xFE10<=ord(ch)<=0xFE4F or 0x3000<=ord(ch)<=0x30FF or 0xF900<=ord(ch)<=0xFAFF)
out = {}
for part in sorted(glob.glob('book/chars_*.json')):
    tag = part.split('_')[1].split('.')[0]; start = int(tag[:3])
    for pi, pg in enumerate(json.load(open(part))):
        chars = []
        for c in pg:
            t = c['t']
            k = f"{tag}|{c['f']}|{c['cid']}"
            if k in gm and not TR(t): t = fix(k)
            t = unicodedata.normalize('NFKC', t) if (0x2E80 <= ord(t[0]) <= 0x2FDF or 0xFE10 <= ord(t[0]) <= 0xFE4F) else t
            chars.append(dict(c, t=t))
        # drop header/footer (copyright, page no, running title): y outside body
        body = [c for c in chars if 60 < c['y0'] < 780 and 'COPYRIGHT' not in c['t']]
        # detect vertical: many chars sharing same x0 within column
        xs = {}
        for c in body: xs.setdefault(round(c['x0']), []).append(c)
        vert = sum(1 for v in xs.values() if len(v) >= 6) >= 2 and sum(len(v) for v in xs.values() if len(v)>=6) > 0.6*len(body)
        if vert:
            cols = []
            for c in sorted(body, key=lambda c: -c['x0']):
                for col in cols:
                    if abs(col[0]['x0'] - c['x0']) < c['s'] * 0.45: col.append(c); break
                else: cols.append([c])
            lines = [''.join(ch['t'] for ch in sorted(col, key=lambda c: -c['y0'])) for col in cols]
        else:
            rows = []
            for c in sorted(body, key=lambda c: -c['y0']):
                for row in rows:
                    if abs(row[0]['y0'] - c['y0']) < c['s'] * 0.45: row.append(c); break
                else: rows.append([c])
            lines = [''.join(ch['t'] for ch in sorted(row, key=lambda c: c['x0'])) for row in rows]
        out[start + pi] = dict(vertical=vert, lines=[l.rstrip() for l in lines])
json.dump(out, open('book/pages.json', 'w'), ensure_ascii=False, indent=0)
for n in [10, 11, 12, 13]:
    print(f'===== PDF {n}', out[n]['vertical'])
    print('\n'.join(out[n]['lines']))
