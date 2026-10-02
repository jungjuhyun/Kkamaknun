# pdfminer로 글자마다 (글꼴 이름, cid, 텍스트, 위치)를 뽑는다
import sys, json
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar
from pdfminer.pdfpage import PDFPage

class Agg(PDFPageAggregator):
    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        try:
            text = font.to_unichr(cid)
        except Exception:
            text = f"(cid:{cid})"
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTChar(matrix, font, fontsize, scaling, rise, text, textwidth, textdisp, ncs, graphicstate)
        item.cid = cid
        self.cur_item.add(item)
        return item.adv

def walk(o, out):
    if isinstance(o, LTChar):
        out.append(o)
    elif hasattr(o, '__iter__'):
        for x in o: walk(x, out)

def extract(path):
    rm = PDFResourceManager()
    dev = Agg(rm, laparams=None)
    it = PDFPageInterpreter(rm, dev)
    pages = []
    with open(path, 'rb') as f:
        for pg in PDFPage.get_pages(f):
            it.process_page(pg)
            lay = dev.get_result()
            chars = []
            walk(lay, chars)
            pages.append([dict(f=c.fontname, cid=c.cid, t=c.get_text(), x0=c.x0, y0=c.y0, x1=c.x1, y1=c.y1, s=c.size, up=c.upright) for c in chars])
    return pages

if __name__ == '__main__':
    pages = extract(sys.argv[1])
    json.dump(pages, open(sys.argv[2], 'w'), ensure_ascii=False)
    print(len(pages), sum(len(p) for p in pages))
