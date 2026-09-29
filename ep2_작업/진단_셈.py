# 1편 판정표로 "어떤 대사에서 막히는가"를 센다.
# 사용: python 진단_셈.py 판정표.xlsx
# 대상: 따라함·옮김·추측·못알아들음 줄 (확인 불가 뺌). 판정은 Claude 판정 그대로.
# "동사 뒤에 붙는 말" = 조동사(ない·た·れる·せる 등) + 보조동사(いる·しまう 등) + 접속조사(て·ば 등). janome로 나눔.
import sys, re, collections, openpyxl
from janome.tokenizer import Tokenizer

t = Tokenizer()
wb = openpyxl.load_workbook(sys.argv[1])
rows = [r for r in wb['판정'].iter_rows(min_row=2, values_only=True)
        if r[3] in ('따라함', '옮김', '추측', '못알아들음') and r[5] != '확인 불가']

data = []
for r in rows:
    s = re.sub(r'（[^）]*）|\([^)]*\)|\[추정\]', '', r[4] or '')
    pos = [x.part_of_speech.split(',') for x in t.tokenize(s)]
    aux = sum(1 for p in pos if p[0] == '助動詞' or (p[0] == '動詞' and p[1] == '非自立')
              or (p[0] == '助詞' and p[1] == '接続助詞'))
    n = len(re.sub(r'[\s…！？!?、。～ー・/]', '', s))
    data.append((n, aux, r[5] == '맞음'))

def show(label, sel):
    k = len(sel); o = sum(d[2] for d in sel)
    print(f'{label}: {k}줄, 맞음 {o} ({round(o * 100 / k)}%)')

show('전체', data)
show('8자 이하', [d for d in data if d[0] <= 8])
show('9~15자', [d for d in data if 9 <= d[0] <= 15])
show('16자 이상', [d for d in data if d[0] >= 16])
for lo, hi, name in [(9, 15, '9~15자'), (16, 999, '16자 이상'), (9, 999, '9자 이상')]:
    sub = [d for d in data if lo <= d[0] <= hi]
    show(f'{name}, 동사 뒤에 붙는 말 0~1개', [d for d in sub if d[1] <= 1])
    show(f'{name}, 동사 뒤에 붙는 말 2개 이상', [d for d in sub if d[1] >= 2])
