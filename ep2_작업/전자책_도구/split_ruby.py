import json, functools
K = json.load(open('kanji.json'))
DAK = dict(zip('かきくけこさしすせそたちつてとはひふへほ', 'がぎぐげござじずぜぞだぢづでどばびぶべぼ'))
HAN = dict(zip('はひふへほ', 'ぱぴぷぺぽ'))
def base_readings(ch):
    d = K.get(ch)
    if not d: return set()
    out = set()
    for r in (d.get('readings_on') or []) + (d.get('readings_kun') or []):
        r = r.replace('-', '').split('.')[0]
        r = ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in r)
        if r: out.add(r)
    return out
def variants(rs):
    out = set(rs)
    for r in rs:
        if r[0] in DAK: out.add(DAK[r[0]] + r[1:])
        if r[0] in HAN: out.add(HAN[r[0]] + r[1:])
        if len(r) > 1 and r[-1] in 'つくちき': out.add(r[:-1] + 'っ')
        if len(r) > 1 and r[-1] in 'ちつ': out.add(r[:-1])
    for r in list(out):
        if r[0] in DAK and len(r) > 1 and r[-1] in 'つくちき': out.add(DAK[r[0]] + r[1:-1] + 'っ')
    return out
def split(word, reading):
    chars = list(word)
    cands = []
    for i, ch in enumerate(chars):
        if ch == '々' and i > 0: cands.append(variants(base_readings(chars[i-1])))
        else: cands.append(variants(base_readings(ch)))
    if any(not c for c in cands): return None
    @functools.lru_cache(None)
    def go(i, pos):
        if i == len(chars): return () if pos == len(reading) else None
        for r in sorted(cands[i], key=len, reverse=True):
            if reading.startswith(r, pos):
                rest = go(i + 1, pos + len(r))
                if rest is not None: return (r,) + rest
        return None
    return go(0, 0)
if __name__ == '__main__':
    for w, r in [('時代','じだい'),('勉強法','べんきょうほう'),('日本語','にほんご'),('様々','さまざま'),('一冊','いっさつ'),('大人','おとな'),('今日','きょう'),('元々','もともと'),('一生懸命','いっしょうけんめい'),('学校','がっこう'),('商人','しょうにん'),('非効率的','ひこうりつてき'),('人見知','ひとみし')]:
        print(w, r, split(w, r))
