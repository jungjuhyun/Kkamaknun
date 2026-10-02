# 가나 읽기를 한글 소리로 바꾼다. 가나 한 글자씩 그대로 옮기고(おう→오우), ー는 그대로 둔다.
# っ는 앞 글자 받침 ㅅ, ん은 앞 글자 받침 ㄴ.
import re, unicodedata

base = dict(zip('あいうえお', '아이우에오'))
base.update(zip('かきくけこ', '카키쿠케코')); base.update(zip('がぎぐげご', '가기구게고'))
base.update(zip('さしすせそ', '사시스세소')); base.update(zip('ざじずぜぞ', '자지즈제조'))
base.update(zip('たちつてと', '타치츠테토')); base.update(zip('だぢづでど', '다지즈데도'))
base.update(zip('なにぬねの', '나니누네노')); base.update(zip('はひふへほ', '하히후헤호'))
base.update(zip('ばびぶべぼ', '바비부베보')); base.update(zip('ぱぴぷぺぽ', '파피푸페포'))
base.update(zip('まみむめも', '마미무메모')); base.update(zip('やゆよ', '야유요'))
base.update(zip('らりるれろ', '라리루레로')); base.update(zip('わゐゑを', '와이에오'))
base.update({'ゔ': '부', 'ぁ': '아', 'ぃ': '이', 'ぅ': '우', 'ぇ': '에', 'ぉ': '오',
             'ゃ': '야', 'ゅ': '유', 'ょ': '요', 'ゎ': '와'})
# 작은 ゃゅょ와 붙는 소리
yo = {}
for k, h in zip('きしちにひみりぎじびぴ', ['캬큐쿄', '샤슈쇼', '차추초', '냐뉴뇨', '햐휴효', '먀뮤묘',
                                          '랴류료', '갸규교', '자주조', '뱌뷰뵤', '퍄퓨표']):
    for s, hh in zip('ゃゅょ', h):
        yo[k + s] = hh
yo['ぢゃ'], yo['ぢゅ'], yo['ぢょ'] = '자', '주', '조'
# 작은 ぁぃぅぇぉ와 붙는 소리 (주로 가타카나 외래어)
small = {'ふぁ': '화', 'ふぃ': '피', 'ふぇ': '페', 'ふぉ': '포', 'ふゅ': '휴',
         'てぃ': '티', 'でぃ': '디', 'とぅ': '투', 'どぅ': '두', 'でゅ': '듀', 'てゅ': '튜',
         'うぃ': '위', 'うぇ': '웨', 'うぉ': '워', 'しぇ': '셰', 'じぇ': '제', 'ちぇ': '체',
         'ゔぁ': '바', 'ゔぃ': '비', 'ゔぇ': '베', 'ゔぉ': '보', 'つぁ': '차', 'つぃ': '치',
         'つぇ': '체', 'つぉ': '초', 'いぇ': '예', 'くぁ': '콰', 'ぐぁ': '과', 'きぇ': '케'}
pairs = {**yo, **small}


def to_hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' and c not in 'ヵヶ' else c for c in s)


def add_final(syl, jong):  # jong: 4=ㄴ, 19=ㅅ
    code = ord(syl) - 0xAC00
    if 0 <= code < 11172 and code % 28 == 0:
        return chr(ord(syl) + jong)
    return None


def convert(s):
    """가나 문자열 → 한글 소리. 숫자는 그대로, 그 밖의 기호·영문·문장부호는 뺀다."""
    s = unicodedata.normalize('NFKC', s)
    h = to_hira(s)
    out = []
    i = 0
    while i < len(h):
        c = h[i]
        two = h[i:i + 2]
        if two in pairs:
            out.append(pairs[two]); i += 2; continue
        if c in base:
            out.append(base[c])
        elif c == 'ん':
            if out and (n := add_final(out[-1], 4)):
                out[-1] = n
            else:
                out.append('응')
        elif c == 'っ':
            if out and (n := add_final(out[-1], 19)):
                out[-1] = n
            elif not out or not ('가' <= out[-1][-1] <= '힣'):
                out.append('읏')  # 글자 이름으로 혼자 나온 っ
            # 이미 받침이 있으면(찬っ) 따로 적지 않는다
        elif c in 'ー〜～':
            out.append('ー')
        elif c in 'ゝ' and out:
            out.append(out[-1])
        elif c.isdigit():
            out.append(c)
        elif c in ' /・' and out and out[-1] != ' ':
            out.append(' ')
        i += 1
    return ''.join(out).strip()


def reading(seg):
    """`{漢字|よみ}` 표시가 든 일본어 덩어리 → 읽는 가나.
    조사 は·へ(괄호 밖 글자, 덩어리 끝이나 문장부호 앞)는 わ·え로 읽는다."""
    parts = []  # (가나, 괄호밖인가)
    i = 0
    for m in re.finditer(r'\{([^|{}]+)\|([^{}]+)\}', seg):
        parts.append((seg[i:m.start()], True)); parts.append((m.group(2), False)); i = m.end()
    parts.append((seg[i:], True))
    flat = []
    for t, outside in parts:
        for ch in t:
            flat.append([ch, outside])
    kana = lambda ch: '぀' <= ch <= 'ヿ'
    for idx, (ch, outside) in enumerate(flat):
        if not outside or ch not in 'はへ':
            continue
        nxt = next((c for c, _ in flat[idx + 1:] if c.strip()), '')
        prev_kana = idx > 0 and (kana(flat[idx - 1][0]) or not flat[idx - 1][1])
        if not prev_kana:
            continue
        if ch == 'は' and (not nxt or not kana(nxt)):
            flat[idx][0] = 'わ'
        if ch == 'へ' and (not nxt or not kana(nxt) or nxt in 'とのは'):
            flat[idx][0] = 'え'
    return ''.join(ch for ch, _ in flat)


if __name__ == '__main__':
    for t in ['{日本語|にほんご}', 'ちょっと', 'こんにちは', '{学校|がっこう}へ', 'コーヒーは', 'さあー', 'では']:
        print(t, '→', convert(reading(t)))
