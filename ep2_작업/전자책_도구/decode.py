import json, glob, unicodedata, collections, io
import numpy as np, freetype, pymupdf
from fontTools.ttLib import TTFont

SIZE=48; W=64; OX=8; OY=52
def render(face, gid):
    face.set_pixel_sizes(0, SIZE)
    face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    g = face.glyph; bm = g.bitmap
    a = np.zeros((W, W), np.float32)
    if bm.width == 0 or bm.rows == 0: return a
    buf = np.array(bm.buffer, np.float32).reshape(bm.rows, bm.pitch)[:, :bm.width] / 255
    x = OX + g.bitmap_left; y = OY - g.bitmap_top
    xs, ys = max(0, x), max(0, y); xe, ye = min(W, x + bm.width), min(W, y + bm.rows)
    if xe > xs and ye > ys:
        a[ys:ye, xs:xe] = buf[ys - y:ye - y, xs - x:xe - x]
    return a

def trusted(ch):
    if len(ch) != 1: return False
    o = ord(ch)
    return (0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0x2E80 <= o <= 0x2FDF or 0xAC00 <= o <= 0xD7AF
            or 0x3130 <= o <= 0x318F or 0x1100 <= o <= 0x11FF or 0xFE10 <= o <= 0xFE4F or 0x3000 <= o <= 0x30FF or 0xF900 <= o <= 0xFAFF)

RANGES = [(0x21,0x7E),(0xA1,0x24F),(0x250,0x2FF),(0x370,0x3FF),(0x2010,0x206F),(0x2190,0x21FF),(0x2460,0x24FF),(0x25A0,0x27BF),(0x3000,0x30FF),(0xFF01,0xFF65),(0x2200,0x22FF)]
def ref_bank(path):
    tt = TTFont(path); cmap = tt.getBestCmap(); order = tt.getGlyphOrder(); g2i = {n:i for i,n in enumerate(order)}
    face = freetype.Face(path)
    labels, gids = [], []
    for cp, gn in cmap.items():
        if any(a <= cp <= b for a, b in RANGES):
            labels.append(chr(cp)); gids.append(g2i[gn])
    # vertical alternates
    if 'GSUB' in tt:
        rev = collections.defaultdict(list)
        for cp, gn in cmap.items():
            if any(a <= cp <= b for a, b in RANGES): rev[gn].append(chr(cp))
        gsub = tt['GSUB'].table
        for fr in gsub.FeatureList.FeatureRecord:
            if fr.FeatureTag in ('vert', 'vrt2'):
                for li in fr.Feature.LookupListIndex:
                    lk = gsub.LookupList.Lookup[li]
                    for st in lk.SubTable:
                        st = getattr(st, 'ExtSubTable', st)
                        if hasattr(st, 'mapping'):
                            for src, dst in st.mapping.items():
                                if src in rev:
                                    labels.append(rev[src][0]); gids.append(g2i[dst])
    mats = np.stack([render(face, g).ravel() for g in gids])
    norms = np.linalg.norm(mats, axis=1); norms[norms == 0] = 1
    return labels, mats / norms[:, None]

banks = {w: ref_bank(f'ref_{w}.ttf') for w in ['Regular', 'Bold', 'Black']}
banks['IPA'] = ref_bank('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf') if glob.glob('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf') else None
print({k: len(v[0]) for k, v in banks.items() if v})

def bank_for(fontname):
    if 'NotoSansKR' in fontname:
        return 'Black' if 'Black' in fontname else 'Bold' if 'Bold' in fontname else 'Regular'
    if 'MS-Gothic' in fontname or 'HiraMin' in fontname: return 'IPA'
    return None

result = {}
for part in sorted(glob.glob('book/chars_*.json')):
    tag = part.split('_')[1].split('.')[0]
    pages = json.load(open(part))
    doc = pymupdf.open(f'book/p_{tag}.pdf')
    fontbuf = {}
    for p in doc:
        for xref, ext, typ, base, nm, enc in p.get_fonts():
            if base not in fontbuf:
                try:
                    fontbuf[base] = doc.extract_font(xref)[3]
                except Exception: pass
    need = set()
    for pg in pages:
        for c in pg:
            if bank_for(c['f']) and not trusted(c['t']) and c['t'].strip():
                need.add((c['f'], c['cid']))
    faces = {}
    for fname, cid in sorted(need):
        key = f"{tag}|{fname}|{cid}"
        buf = fontbuf.get(fname)
        if not buf: result[key] = ('?', 0, '?', 0); continue
        if fname not in faces:
            tt = TTFont(io.BytesIO(buf)); cm = {}
            for t in tt['cmap'].tables:
                for code, gn in t.cmap.items(): cm.setdefault(code & 0xFF if t.platformID == 3 and t.platEncID == 0 else code, tt.getGlyphID(gn))
            faces[fname] = (freetype.Face(io.BytesIO(buf)), cm)
        face, cm = faces[fname]
        gid = cm.get(cid)
        if gid is None: result[key] = ('?', 0, '?', 0); continue
        v = render(face, gid).ravel(); n = np.linalg.norm(v)
        if n == 0: result[key] = (' ', 1, ' ', 1); continue
        labels, mats = banks[bank_for(fname)]
        sc = mats @ (v / n); o = np.argsort(-sc)
        # second best with different label
        best = labels[o[0]]; sec = next((labels[i], float(sc[i])) for i in o[1:] if labels[i] != best)
        result[key] = (best, float(sc[o[0]]), sec[0], sec[1])
json.dump(result, open('book/glyphmap.json', 'w'), ensure_ascii=False)
low = {k: v for k, v in result.items() if v[1] < 0.9 or v[1] - v[3] < 0.03}
print(len(result), 'low', len(low))
for k, v in list(low.items())[:60]: print(k, v)
