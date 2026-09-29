# 1편 판정표에서 문법 항목별로 "그 항목이 든 대사"의 맞음 비율을 센다.
# 사용: python 문법_셈.py 판정표.xlsx
# 대상: 따라함·옮김·추측·못알아들음 줄(확인 불가 뺌). 판정은 Claude 판정 그대로. 형태소 분석은 janome.
import sys, re, collections, openpyxl
from janome.tokenizer import Tokenizer

t = Tokenizer()
GODAN_END = {'える': 'う', 'ける': 'く', 'げる': 'ぐ', 'せる': 'す', 'てる': 'つ', 'ねる': 'ぬ', 'べる': 'ぶ', 'める': 'む', 'れる': 'る'}
# 자동사·타동사 짝이라 가능형이 아닌 것 (검사해서 넣음)
NOT_POTENTIAL = {'かける', '続ける', '開ける', '見せる', '助ける', '付ける', 'つける', '届ける', '向ける', '上げる', 'あげる',
                 '下げる', '逃げる', '分ける', '決める', '止める', 'やめる', '始める', '集める', '閉める', '入れる', '忘れる',
                 '生まれる', '離れる', '触れる', '慣れる', '晴れる', '流れる', '別れる', '壊れる', '遅れる', '疲れる', '見つける',
                 '片付ける', '受ける', '抜ける', '育てる', '建てる', '立てる', '捨てる', '当てる', '寝る', '見える', '聞こえる', '消える', '燃える', '増える', '教える', '考える', '覚える', '変える', '答える', '伝える', '揃える', '迎える', '抱える', '震える', '冷える', '越える', '超える', '仕える', '与える', '植える', '数える', '訴える', '生える', '吠える', '甘える', '構える', '支える', '整える', '据える', '終える', '控える', '備える', '唱える', '称える', '加える', '押さえる', '抑える', '捕まえる', '捕らえる', '間違える', '着替える', '乗り換える', '見上げる', '逃れる', '隠れる', '崩れる', '汚れる', '倒れる', '外れる', '暮れる', '揺れる', '濡れる', '溢れる', '恐れる', '憧れる', '現れる', '溺れる', '取れる', '切れる', '売れる', '折れる', '割れる', '剥がれる', '連れる', '焼ける', '負ける', '避ける', '明ける', '欠ける', '溶ける', '解ける', '掛ける', '出かける', '出掛ける', '追いかける', '話しかける', '呼びかける', '見かける', '投げる', '曲げる', '広げる', '揚げる', '挙げる', '告げる', '妨げる', '仕上げる', '申し上げる', '絡める', '求める', '認める', '勧める', '進める', '確かめる', '詰める', '責める', '攻める', '占める', '染める', '褒める', '眺める', '諦める', '固める', '温める', '暖める', '高める', '強める', '深める', '努める', '勤める', '務める', '含める', '込める', '締める', '絞める', '閉じ込める', '比べる', '並べる', '調べる', '述べる', '食べる', '浮かべる', '混ぜる', '乗せる', '載せる', '寄せる', '任せる', '合わせる', '見せる', '知らせる', '済ませる', '尖らせる', '持てる', '捨てる'}

def potential(tok):
    b = tok.base_form
    p = tok.part_of_speech.split(',')
    if p[0] != '動詞' or p[1] != '自立' or tok.infl_type != '一段' or b in NOT_POTENTIAL:
        return False
    if b == 'できる' or b == '出来る':
        return True
    for e, g in GODAN_END.items():
        if b.endswith(e) and len(b) > 2:
            cand = b[:-2] + g
            ts = list(t.tokenize(cand))
            if len(ts) == 1 and ts[0].part_of_speech.startswith('動詞') and ts[0].infl_type.startswith('五段'):
                return True
    return False

CAUS = {'かせる': 'く', 'がせる': 'ぐ', 'させる': 'す', 'たせる': 'つ', 'なせる': 'ぬ', 'ばせる': 'ぶ', 'ませる': 'む', 'らせる': 'る', 'わせる': 'う'}
def causative(tok):
    p = tok.part_of_speech.split(',')
    if p[0] == '動詞' and p[1] == '接尾' and tok.base_form in ('せる', 'させる'):
        return True
    if p[0] == '助動詞' and tok.base_form in ('せる', 'させる'):
        return True
    b = tok.base_form
    if p[0] == '動詞' and p[1] == '自立' and b not in NOT_POTENTIAL:
        for e, g in CAUS.items():
            if b.endswith(e) and len(b) > 3:
                ts = list(t.tokenize(b[:-3] + g))
                if len(ts) == 1 and ts[0].part_of_speech.startswith('動詞') and ts[0].infl_type.startswith('五段'):
                    return True
    return False

def items(s):
    toks = list(t.tokenize(s))
    found = set()
    for i, x in enumerate(toks):
        p = x.part_of_speech.split(',')
        b, f, sf = x.base_form, x.infl_form, x.surface
        prev = toks[i - 1] if i else None
        if p[0] == '助詞' and p[1] == '接続助詞' and b in ('て', 'で'):
            found.add('て형 (~하고, ~해서)')
        if p[0] == '動詞' and p[1] == '非自立' and b in ('いる', 'てる', 'でる', 'とる', 'どる'):
            found.add('~ている·~てる (~하고 있다)')
        if p[0] == '助動詞' and (b in ('ない', 'ぬ') or (b == 'ん' and x.infl_type == '特殊・ヌ')):
            found.add('ない형 (안 ~)')
        if p[0] == '助動詞' and x.infl_type == '特殊・タ':
            found.add('た형 (~했다)')
        if p[0] == '助動詞' and b == 'ます':
            found.add('ます형 (~합니다)')
        if potential(x):
            found.add('가능형 (~할 수 있다)')
        if (p[0] == '動詞' and p[1] == '接尾' and b in ('れる', 'られる')) or (p[0] == '助動詞' and b in ('れる', 'られる')):
            found.add('れる·られる (~당하다, 수동)')
        if causative(x):
            found.add('사역형 (~시키다, ~하게 하다)')
        if p[0] == '動詞' and p[1] == '非自立' and b in ('しまう', 'ちゃう', 'じゃう', 'ちまう', 'じまう'):
            found.add('~てしまう·~ちゃう (~해 버리다)')
        if p[0] == '動詞' and p[1] == '非自立' and b == 'すぎる':
            found.add('~すぎる (너무 ~하다)')
        if p[0] == '助動詞' and b == 'たい':
            found.add('~たい (~하고 싶다)')
        if p[0] == '助動詞' and b in ('う', 'よう') and x.infl_type == '不変化型':
            found.add('의지형 ~よう (~하자, ~하려고)')
        if (p[0] == '助詞' and p[1] == '接続助詞' and b == 'ば') or f.startswith('仮定') or (p[0] == '助動詞' and x.infl_type == '特殊・タ' and f == '仮定形'):
            found.add('조건형 ~ば·~たら (~하면)')
        if b == 'よう' and p[0] == '名詞' and i + 1 < len(toks) and toks[i + 1].surface == 'に':
            found.add('~ように (~하도록, ~하게 되다)')
        if f.startswith('命令'):
            found.add('명령형 (~해라)')
        if p[0] == '動詞' and p[1] == '非自立' and b in ('くれる', 'もらう', 'あげる', 'やる', 'くださる', 'いただく'):
            found.add('~てくれる·~てもらう (주고받기)')
        if p[0] == '助詞' and b == 'しか':
            found.add('しか~ない (~밖에 안)')
        if p[0] == '名詞' and p[1] == '非自立' and b in ('ん', 'の') and i + 1 < len(toks) and toks[i + 1].base_form in ('だ', 'です'):
            found.add('~んだ (~인 거야, 설명)')
    return found

if __name__ == '__main__':
    wb = openpyxl.load_workbook(sys.argv[1])
    rows = [r for r in wb['판정'].iter_rows(min_row=2, values_only=True)
            if r[3] in ('따라함', '옮김', '추측', '못알아들음') and r[5] != '확인 불가']
    base = sum(r[5] == '맞음' for r in rows) / len(rows)
    stat = collections.defaultdict(lambda: [0, 0, []])
    for r in rows:
        s = re.sub(r'（[^）]*）|\([^)]*\)|\[추정\]', '', r[4] or '')
        for it in items(s):
            st = stat[it]
            st[0] += 1
            st[1] += r[5] == '맞음'
            if r[5] != '맞음':
                st[2].append(f'{r[1]} {s.strip()} [{r[5]}]')
    print(f'전체 {len(rows)}줄, 맞음 {round(base * 100)}%')
    print()
    for it, (n, ok, bad) in sorted(stat.items(), key=lambda kv: kv[1][1] / kv[1][0]):
        print(f'{it}: {n}줄, 맞음 {ok} ({round(ok * 100 / n)}%)')
        for b in bad:
            print('    ', b)
