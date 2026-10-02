# 전자책 PDF를 몇 쪽씩 나눠서, 대화창에 올릴 수 있는 크기로 만든다.
# 쓰는 법: python 책나누기.py "C:\kkamaknun\책이름.pdf" [한 파일당 쪽 수, 기본 20]
# 결과: 같은 폴더의 "책이름_나눔" 폴더에 저장된다. 파일마다 크기(MB)를 보여 준다.
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

src = Path(sys.argv[1])
per = int(sys.argv[2]) if len(sys.argv) > 2 else 20

reader = PdfReader(src)
total = len(reader.pages)
out_dir = src.parent / f"{src.stem}_나눔"
out_dir.mkdir(exist_ok=True)

for start in range(0, total, per):
    end = min(start + per, total)
    writer = PdfWriter()
    for i in range(start, end):
        writer.add_page(reader.pages[i])
    out = out_dir / f"{src.stem}_{start + 1:03d}-{end:03d}쪽.pdf"
    with open(out, "wb") as f:
        writer.write(f)
    print(f"{out.name}  {out.stat().st_size / 1_000_000:.1f}MB")

print(f"전체 {total}쪽 → {out_dir}")
