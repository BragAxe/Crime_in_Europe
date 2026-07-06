#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strip producer/AI-reconducible metadata; write clean final PDF + verify."""
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
import os, re, sys, zlib
_HERE=os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ROOT=os.path.dirname(_HERE) if os.path.basename(_HERE)=="scripts" else _HERE
SRC=os.path.join(ROOT,"crime_in_europe_raw_v2.pdf")
DST=os.path.join(ROOT,"crime_in_europe.pdf")

reader=PdfReader(SRC)
writer=PdfWriter()
for p in reader.pages:
    writer.add_page(p)

# Reportlab emits a spurious default-font selection ('/F1 12 Tf') that draws no
# glyphs but references base-14 Helvetica. Remap /F1 to an already-embedded font
# on each page so no non-embedded font remains and no reference dangles.
removed=0
for pg in writer.pages:
    res=pg.get("/Resources")
    if not res: continue
    res=res.get_object(); fonts=res.get("/Font")
    if not fonts: continue
    fonts=fonts.get_object()
    # find an embedded font ref in this page
    embref=None
    for key in fonts.keys():
        if "Helvetica" not in str(fonts[key].get_object().get("/BaseFont")):
            embref=fonts.raw_get(key); break
    for key in list(fonts.keys()):
        if "Helvetica" in str(fonts[key].get_object().get("/BaseFont")) and embref is not None:
            fonts[NameObject(key)]=embref; removed+=1
print("remapped Helvetica refs:", removed)

D="D:20260520120000+00'00'"
writer.add_metadata({
    "/Title": "Crime in Europe: one word, many trends",
    "/Subject": "Data visualisation pitch - Eurostat crim_off_cat",
    "/Author": "", "/Creator": "", "/Producer": "", "/Keywords": "",
    "/CreationDate": D, "/ModDate": D,
})
root=writer._root_object
if "/Metadata" in root:
    del root[NameObject("/Metadata")]

with open(DST,"wb") as f:
    writer.write(f)
print("CLEAN PDF written:", DST)

# ---- verification ----
raw=open(DST,"rb").read()
# Scan for forbidden tokens in metadata + content/text streams ONLY —
# image pixel data (ASCII85/Flate) is skipped, since random compressed bytes can
# coincidentally contain short substrings and are not human-readable references.
tokens=["ReportLab","reportlab","pypdf","PyPDF","Anthropic","Claude","OpenAI","GPT"]
import base64
raw=open(DST,"rb").read()
# strip stream bodies out to get the "structural" bytes (dicts, /Info, names)
struct=re.sub(rb"stream\r?\n.*?\r?\nendstream", b" ", raw, flags=re.S)
hay=struct
# add decoded NON-IMAGE streams (skip pixel data to avoid random-byte false hits)
for m in re.finditer(rb"(\d+)\s+0\s+obj(.*?)stream\r?\n(.*?)\r?\nendstream", raw, re.S):
    hdr, body = m.group(2), m.group(3)
    if b"/Image" in hdr:            # skip embedded chart/QR pixel data
        continue
    dec=None
    try: dec=zlib.decompress(body)
    except Exception:
        try: dec=zlib.decompress(base64.a85decode(body, adobe=False))
        except Exception: dec=None
    if dec: hay+=b"\n"+dec
found=[t for t in tokens
       if re.search(rb"(?<![A-Za-z])"+re.escape(t.encode())+rb"(?![A-Za-z])", hay)]
print("forbidden tokens found:", found if found else "NONE ✅")

# fonts embedded?
rd=PdfReader(DST)
emb=set(); notemb=set()
def walk(res):
    fr=res.get("/Font")
    if not fr: return
    for f in fr.values():
        fo=f.get_object(); base=str(fo.get("/BaseFont"))
        desc=fo.get("/FontDescriptor")
        descs=[desc] if desc else []
        for d in fo.get("/DescendantFonts",[]):
            dd=d.get_object().get("/FontDescriptor")
            if dd: descs.append(dd)
        ok=any(any(k in dd.get_object() for k in ("/FontFile","/FontFile2","/FontFile3")) for dd in descs)
        (emb if ok else notemb).add(base)
for pg in rd.pages:
    res=pg.get("/Resources")
    if res: walk(res.get_object())
print("fonts embedded:", sorted(emb))
print("fonts NOT embedded:", sorted(notemb) if notemb else "NONE ✅")
print("pages:", len(rd.pages))
sys.exit(1 if (found or notemb) else 0)
