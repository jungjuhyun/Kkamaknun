# 편집본 쪽(png)을 원래 책 PDF의 같은 쪽 자리에 넣어, 원래 책과 같은 순서의 PDF 하나로 만든다.
# 쓰는 법: python 쪽합치기.py <src 폴더> <png 폴더> <나눈 원본 PDF 폴더> <결과.pdf>
# 책 쪽 = PDF 쪽 - 2. "127~128쪽"처럼 두 쪽을 묶은 편집본은 뒤쪽 번호 자리에 넣는다.
# 원본 쪽은 그림(JPEG)으로 바꿔 넣는다. 대화창으로 보낼 수 있는 30MB 아래로 맞추기 위해서다.
import sys, glob, re, os, io
import pymupdf as fitz
from PIL import Image

src_dir, png_dir, book_dir, out_path = sys.argv[1:5]
names = []
for f in sorted(glob.glob(f'{src_dir}/*.txt')):
    for l in open(f, encoding='utf-8'):
        if l.startswith('#'): names.append(l[1:].strip())
fs = sorted(glob.glob(f'{png_dir}/*.png'),
            key=lambda p: (os.path.basename(p).rsplit('_', 1)[0], int(re.search(r'_(\d+)\.png', p).group(1))))
assert len(names) == len(fs), (len(names), len(fs))
ed = {int(re.findall(r'\d+', n)[-1]): p for n, p in zip(names, fs)}

def jpg(im, q):
    buf = io.BytesIO(); im.convert('RGB').save(buf, 'JPEG', quality=q, optimize=True); return buf.getvalue()

out = fitz.open()
for part in sorted(glob.glob(f'{book_dir}/p_*.pdf')):
    src = fitz.open(part); s0 = int(re.search(r'p_(\d+)', part).group(1))
    for i in range(len(src)):
        b = s0 + i - 2; r = src[i].rect; pg = out.new_page(width=r.width, height=r.height)
        if b in ed:
            data = jpg(Image.open(ed[b]), 80)
        else:
            pix = src[i].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            data = jpg(Image.frombytes('RGB', (pix.width, pix.height), pix.samples), 75)
        pg.insert_image(r, stream=data, keep_proportion=True)
out.save(out_path, garbage=4, deflate=True)
print(len(out), '쪽', round(os.path.getsize(out_path) / 2**20, 1), 'MiB')
