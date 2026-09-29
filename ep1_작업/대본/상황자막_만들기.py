"""Subtitle Edit에서 반응 상황을 적을 수 있게 자막 두 개를 만든다.

- 내말_확정.srt: 까막눈_1편_완료.srt(사용자가 고친 자막)를 표준 SRT로 바꾼 것. 글자는 그대로.
- 상황.srt: 같은 시각, 같은 칸 수. 칸마다 상황을 적는 자리.
  - "AI: 종류 | 설명" = 까막눈_1편_반응표기.srt에 AI가 붙였던 설명을 옮긴 것(짐작)
  - "□" = 반응 소리(음?, 어?!, 웃음 등)라 새로 적을 곳
  - "-" = 안 적어도 되는 곳(애니 대사를 따라 하거나 옮긴 줄, 숨소리·기침)

칸 순서는 판정표.xlsx 판정 시트의 번호와 같다.
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DONE = ROOT / "까막눈_1편_완료.srt"
MARKED = ROOT / "까막눈_1편_반응표기.srt"
TABLE = ROOT / "ep1_작업" / "분석" / "판정표.xlsx"
OUT_MINE = Path(__file__).parent / "내말_확정.srt"
OUT_SITU = Path(__file__).parent / "상황.srt"

FPS = 48  # 완료.srt(Closed Caption Converter 형식)의 시각은 1초 48프레임
LABELS = "녹화·딴얘기|감정|읽기|예측·의심|이야기 정리|평가|확인 필요"
MARK = re.compile(rf"\s*\(({LABELS})(?::\s*(.*))?\)\s*$")
BREATH = re.compile(r"숨|기침")


def read_ccc(path):
    """00;00;07;38 00;00;09;00 줄과 글자 줄로 된 칸을 읽는다."""
    body = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    body = body.split("<begin subtitles>")[1].split("<end subtitles>")[0]
    cues = []
    for block in body.strip().split("\n\n"):
        lines = block.strip().split("\n")
        start, end = (to_sec(t) for t in lines[0].split())
        cues.append((start, end, "\n".join(lines[1:])))
    return cues


def to_sec(t):
    h, m, s, f = (int(x) for x in t.split(";"))
    return h * 3600 + m * 60 + s + f / FPS


def srt_time(x):
    ms = int(round(x * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def read_srt_text(path):
    body = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    return [" ".join(b.split("\n")[2:]) for b in body.strip().split("\n\n")]


def write_srt(path, cues):
    parts = [f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{t}\n" for i, (s, e, t) in enumerate(cues, 1)]
    path.write_text("\n".join(parts).replace("\n", "\r\n"), encoding="utf-8-sig")


def main():
    cues = read_ccc(DONE)
    marked = read_srt_text(MARKED)
    kinds = pd.read_excel(TABLE, sheet_name="판정")["유형"].tolist()
    assert len(cues) == len(marked) == len(kinds), (len(cues), len(marked), len(kinds))

    situ, count = [], {"AI": 0, "□": 0, "-": 0}
    for (s, e, text), m, kind in zip(cues, marked, kinds):
        hit = MARK.search(m)
        assert MARK.sub("", m).strip() == text.replace("\n", " ").strip(), text
        if hit:
            line = f"AI: {hit.group(1)} | {hit.group(2) or '□'}"
            count["AI"] += 1
        elif kind == "소리·감탄" and not BREATH.search(text):
            line = "□"
            count["□"] += 1
        else:
            line = "-"
            count["-"] += 1
        situ.append((s, e, line))

    write_srt(OUT_MINE, cues)
    write_srt(OUT_SITU, situ)
    print(f"칸 {len(cues)}개", count)


if __name__ == "__main__":
    main()
