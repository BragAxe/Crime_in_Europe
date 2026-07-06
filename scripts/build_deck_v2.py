#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crime in Europe — data-visualisation pitch, v2. 16:9 vector deck, 11 slides."""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE) == "scripts" else _HERE

import qr
from deck_config import STUDENT, URLS, URL_LABELS, DATA_EXTRACT_DATE

A   = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "crime_in_europe_raw_v2.pdf")
W, H = 1280.0, 720.0
TOTAL = 11

# ---------- fonts ----------
F = {
 "sans":  "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
 "sansb": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
 "sansi": "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
 "mono":  "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
 "monob": "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
 "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
 "serifi":"/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
}
NAME = {"sans":"Sans","sansb":"SansB","sansi":"SansI","mono":"Mono",
        "monob":"MonoB","serif":"Serif","serifi":"SerifI"}
for k,p in F.items():
    pdfmetrics.registerFont(TTFont(NAME[k], p))

# ---------- palette ----------
PAPER  = HexColor("#F5F2EB")
CARD   = HexColor("#FFFFFF")
INK    = HexColor("#1B1B25")
MUTE   = HexColor("#6C6C78")
FAINT  = HexColor("#9A958A")
RULE   = HexColor("#D9D4C8")
SLATE  = HexColor("#2C6E6A")
SLATE_D= HexColor("#1F5350")
CRIM   = HexColor("#A6132A")
SAND   = HexColor("#C9C0AE")
GOLD   = HexColor("#C8772E")
SHADOW = Color(0,0,0,0.07)
INK_RGB = (27,27,37)

MX = 84  # left/right margin

# ---------- QR generation (auto, from config URLs) ----------
os.makedirs(A, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
qr.render_png(URLS["code"],      f"{A}/qr_code.png",      ecc='M', scale=8, border=4, dark=INK_RGB)
qr.render_png(URLS["dashboard"], f"{A}/qr_dashboard.png", ecc='M', scale=8, border=4, dark=INK_RGB)

# ---------- helpers ----------
def sw(t,f,s): return pdfmetrics.stringWidth(t,f,s)

def tspace(c,t,x,y,font,size,color,gap=0.0,align="l"):
    w=sw(t,font,size)+gap*max(len(t)-1,0)
    if align=="r": x=x-w
    c.setFillColor(color)
    to=c.beginText(); to.setTextOrigin(x,y); to.setFont(font,size)
    to.setCharSpace(gap); to.textOut(t); to.setCharSpace(0); c.drawText(to)
    return w

def wrap(t,f,s,maxw):
    out=[]
    for paragraph in t.split("\n"):
        words=paragraph.split(); cur=""
        for w in words:
            tt=(cur+" "+w).strip()
            if sw(tt,f,s)<=maxw: cur=tt
            else:
                if cur: out.append(cur)
                cur=w
        out.append(cur)
    return out

def para(c,t,x,y,maxw,f="Sans",s=13,lead=None,col=INK,align="l"):
    lead=lead or s*1.5
    c.setFillColor(col); c.setFont(f,s)
    for ln in wrap(t,f,s,maxw):
        if align=="c": c.drawCentredString(x+maxw/2,y,ln)
        elif align=="r": c.drawRightString(x+maxw,y,ln)
        else: c.drawString(x,y,ln)
        y-=lead
    return y

def eyebrow(c,t,x,y,col=CRIM,sz=10.5,gap=2.2):
    tspace(c,t.upper(),x,y,"MonoB",sz,col,gap=gap)

def chrome(c,page,total=TOTAL):
    c.setFillColor(PAPER); c.rect(0,0,W,H,fill=1,stroke=0)
    tspace(c,"CRIME IN EUROPE",MX,H-44,"Mono",8.5,FAINT,gap=1.6)
    tspace(c,"EUROSTAT · CRIM_OFF_CAT",W-MX,H-44,"Mono",8.5,FAINT,gap=1.6,align="r")
    c.setStrokeColor(RULE); c.setLineWidth(0.8); c.line(MX,H-56,W-MX,H-56)
    c.setStrokeColor(RULE); c.line(MX,52,W-MX,52)
    tspace(c,"Source: Eurostat (crim_off_cat) — police-recorded offences · EU-27 reconstructed by summing member states",
           MX,38,"Mono",8,FAINT,gap=0.4)
    tspace(c,f"{page:02d} / {total:02d}",W-MX,38,"Mono",8,FAINT,gap=0.6,align="r")

def header(c,num,kicker,title,ty=H-150):
    eyebrow(c,f"{num} — {kicker}",MX,H-92)
    c.setFillColor(INK); c.setFont("SansB",40)
    c.drawString(MX,ty,title)
    return ty-30

def card(c,x,y,w,h,r=12,fill=CARD,border=RULE,shadow=True):
    if shadow:
        c.setFillColor(SHADOW); c.roundRect(x+4,y-5,w,h,r,fill=1,stroke=0)
    c.setFillColor(fill); c.setStrokeColor(border); c.setLineWidth(1)
    c.roundRect(x,y,w,h,r,fill=1,stroke=1)

def image_fit(c,path,x,y,w,h,mask=None):
    img=ImageReader(path); iw,ih=img.getSize(); ar=iw/ih
    if w/h>ar: w=h*ar
    else: h=w/ar
    c.drawImage(img,x,y,w,h,mask=mask,preserveAspectRatio=True)
    return w,h

def link_rect(c,url,x,y,w,h):
    c.linkURL(url,(x,y,x+w,y+h),relative=0,thickness=0)

def link_text(c,label,url,x,y,f="MonoB",s=11,col=SLATE,underline=True):
    """Draw a clickable link label with underline; returns its width."""
    w=sw(label,f,s)
    c.setFillColor(col); c.setFont(f,s); c.drawString(x,y,label)
    if underline:
        c.setStrokeColor(col); c.setLineWidth(0.8); c.line(x,y-2.5,x+w,y-2.5)
    link_rect(c,url,x-3,y-5,w+6,s+7)
    return w

# =====================================================================
c=canvas.Canvas(OUT,pagesize=(W,H))
c.setTitle("Crime in Europe — one word, many trends")
c.setSubject("Data visualisation pitch — Eurostat crim_off_cat")
c.setAuthor(""); c.setCreator(""); c.setKeywords("")

# ---------------- 1. COVER ----------------
c.setFillColor(PAPER); c.rect(0,0,W,H,fill=1,stroke=0)
c.setStrokeColor(INK); c.setLineWidth(1.2); c.line(MX,H-70,MX+54,H-70)
eyebrow(c,"DATA VISUALISATION PITCH — INDIVIDUAL ASSIGNMENT",MX,H-92,col=INK,sz=10.5)
c.setFillColor(INK); c.setFont("SansB",60)
for i,ln in enumerate(["CRIME IN EUROPE:","ONE WORD,","MANY TRENDS"]):
    c.drawString(MX,H-178-i*66,ln)
c.setFillColor(CRIM); c.setFont("SansB",60)
c.drawString(MX+sw("MANY TRENDS","SansB",60)+4,H-178-2*66,".")
c.setFillColor(MUTE)
para(c,"Police-recorded offences in the EU, 2008–2024 — why “is crime rising?” has no single answer.",
     MX,H-392,540,f="SerifI",s=15,lead=24,col=MUTE)
iy=146
c.setStrokeColor(CRIM); c.setLineWidth(2); c.line(MX,iy+44,MX,iy-44)
tspace(c,"STUDENT",MX+16,iy+34,"MonoB",8.5,FAINT,gap=1.5)
rows=[("Name",STUDENT["name"]),("ID",STUDENT["id"]),("E-mail",STUDENT["email"])]
yy=iy+12
for lab,val in rows:
    c.setFillColor(MUTE); c.setFont("Mono",11); c.drawString(MX+16,yy,f"{lab:<8}")
    c.setFillColor(INK);  c.setFont("MonoB",11); c.drawString(MX+90,yy,val)
    yy-=22
cw,chh=540,300
cardx=W-MX-cw; cardy=78
card(c,cardx,cardy,cw,chh,r=14)
tspace(c,"EU-27 RECORDED OFFENCES BY CATEGORY · 2024",cardx+24,cardy+chh-26,"MonoB",8,FAINT,gap=1.4)
image_fit(c,f"{A}/cover_chart.png",cardx+20,cardy+18,cw-40,chh-66,mask="auto")
c.setFillColor(FAINT); c.setFont("Mono",7.5)
c.drawRightString(W-MX,cardy-14,"Source: Eurostat (crim_off_cat)")
c.showPage()

# ---------------- 2. RESEARCH QUESTIONS ----------------
chrome(c,2)
header(c,"01","RESEARCH QUESTIONS","Research questions")
by=H-196; bh=118; bw=W-2*MX
c.setFillColor(CARD); c.setStrokeColor(RULE); c.setLineWidth(1)
c.roundRect(MX,by-bh,bw,bh,10,fill=1,stroke=1)
c.setFillColor(CRIM); c.roundRect(MX,by-bh,6,bh,3,fill=1,stroke=0)
eyebrow(c,"PRIMARY RESEARCH QUESTION",MX+30,by-30,col=CRIM,sz=10)
para(c,"Between 2008 and 2024, is police-recorded crime in the EU rising or falling — and does the answer depend on which offence you count, and where?",
     MX+30,by-56,bw-80,f="SansB",s=20,lead=29,col=INK)
subs=[("1","Which offences dominate the volume of recorded crime — and how rare is the gravest, homicide, by comparison?","VIZ 1 · COMPOSITION"),
      ("2","Does the map of crime match its reputation? Where is Europe safest, and does the answer change with the offence?","VIZ 2 · MAP"),
      ("3","How did the pandemic hit high-volume property crime — and has theft since rebounded to pre-COVID levels?","VIZ 3 · TREND"),
      ("4","Which offence is rising fastest over the decade, and how much reflects real incidence versus better reporting?","VIZ 4 · INDEX")]
gut=28
colw=(W-2*MX-3*gut)/4
top=H-352
for i,(n,t,tag) in enumerate(subs):
    x=MX+i*(colw+gut)
    c.setFillColor(SLATE); c.setFont("SansB",42); c.drawString(x,top-36,n)
    c.setStrokeColor(RULE); c.setLineWidth(1); c.line(x,top-52,x+colw,top-52)
    yend=para(c,t,x,top-76,colw,f="Sans",s=12.5,lead=18.5,col=INK)
    tspace(c,tag,x,yend-6,"MonoB",8,CRIM,gap=1.0)
c.showPage()

# ---------------- 3. ABOUT THE DATA ----------------
chrome(c,3)
header(c,"02","ABOUT THE DATA","About the data")
colw=(W-2*MX-56)/2
lx=MX; rx=MX+colw+56; top=H-198
def block(x,y,tag,body,maxw):
    eyebrow(c,tag,x,y,col=CRIM,sz=9.5)
    return para(c,body,x,y-22,maxw,f="Sans",s=12,lead=18.5,col=INK)
y=top
y=block(lx,y,"DATASET","Eurostat — police-recorded offences by category (crim_off_cat), annual from 2008, classified under the UN ICCS. Units: absolute number of offences and rate per 100 000 inhabitants. Extracted "+DATA_EXTRACT_DATE+".",colw)
y-=10
y=block(lx,y,"EU-27 IS RECONSTRUCTED","The export carries no ready-made EU total, so every EU-27 figure here is built by summing the 27 member states (non-members and UK sub-regions excluded) — not read from an aggregate row.",colw)
y-=10
y=block(lx,y,"2024 COVERAGE (STATED HONESTLY)","In 2024 all 27 states report theft, intentional homicide and sexual violence; burglary is reported by 24 and robbery by 26. Partial-coverage totals are labelled as such and never compared as if complete.",colw)
y=top
eyebrow(c,"QUALITY & CAVEATS",rx,y,col=CRIM,sz=9.5); y-=24
caveats=[
 "Police-recorded ≠ actual crime: reporting rates, police practice and national law differ, so cross-country comparison stays cautious.",
 "A 2016 methodological break in the French series (ICCS reclassification) distorts the property-crime trend; this export carries no machine flags, so it is handled as a documented caveat.",
 "ICCS categories are nested (rape sits within sexual violence) — they are never summed naïvely.",
 "For the ‘rising reports’ claim, endpoints use the same country basket (sexual violence 27/27; rape 26/27 with Italy absent in both years) so the change is not a coverage artefact.",
]
for cav in caveats:
    c.setFillColor(CRIM); c.setFont("SansB",12); c.drawString(rx,y,"•")
    yend=para(c,cav,rx+16,y,colw-16,f="Sans",s=11.5,lead=16.5,col=INK)
    y=yend-5
y-=6
eyebrow(c,"DATA CLEANING",rx,y,col=CRIM,sz=9.5)
para(c,"pandas pipeline: filter to the 27 member states, select ICCS categories and the correct unit, keep nested categories separate, reconstruct EU-27 totals per year, and record per-offence coverage. One script regenerates every figure in this deck.",
     rx,y-22,colw,f="Sans",s=11.5,lead=16.5,col=INK)
c.showPage()

# ---------------- 4. METHODOLOGY ----------------
chrome(c,4)
header(c,"03","METHODOLOGY","Methodology")
# Row A — two distinct ecosystems
gut=40; cwid=(W-2*MX-gut)/2; ay=H-196; ah=132
# left: Python static
card(c,MX,ay-ah,cwid,ah,r=12)
c.setFillColor(SLATE); c.roundRect(MX,ay-ah,6,ah,3,fill=1,stroke=0)
tspace(c,"TOOLCHAIN A · STATIC",MX+26,ay-26,"MonoB",8.5,SLATE,gap=1.2)
c.setFillColor(INK); c.setFont("SansB",17); c.drawString(MX+26,ay-48,"Python — analysis & charts")
para(c,"pandas cleans and aggregates the data; Matplotlib and Seaborn render the four editorial figures. Deterministic, print-quality vector output for the deck.",
     MX+26,ay-70,cwid-52,f="Sans",s=11.5,lead=16.5,col=MUTE)
# right: Plotly.js interactive (different ecosystem)
rxc=MX+cwid+gut
card(c,rxc,ay-ah,cwid,ah,r=12)
c.setFillColor(CRIM); c.roundRect(rxc,ay-ah,6,ah,3,fill=1,stroke=0)
tspace(c,"TOOLCHAIN B · INTERACTIVE",rxc+26,ay-26,"MonoB",8.5,CRIM,gap=1.2)
c.setFillColor(INK); c.setFont("SansB",17); c.drawString(rxc+26,ay-48,"Plotly.js — interactive map")
para(c,"A separate, browser-based JavaScript stack renders an interactive European choropleth with an offence selector, hover read-outs and zoom — a functionally different tool from the static Python charts.",
     rxc+26,ay-70,cwid-52,f="Sans",s=11.5,lead=16.5,col=MUTE)
# Row B — three process items
items=[("COLLECTION","Manual export from the Eurostat Data Browser (crim_off_cat), cross-checked against Eurostat’s published crime statistics."),
       ("TRANSFORMATION","Aggregation by offence; base-year indexing (2014 = 100); pandemic trough and rebound derived from the annual series."),
       ("TECHNIQUES","Descriptive statistics, time-series and trend analysis, comparative ranking, and per-100 000 rate normalisation.")]
gut3=40; c3=(W-2*MX-2*gut3)/3; by=ay-ah-34
for i,(tag,body) in enumerate(items):
    x=MX+i*(c3+gut3)
    tspace(c,f"{i+1:02d}",x,by,"MonoB",10,SLATE,gap=1.2)
    c.setFillColor(INK); c.setFont("SansB",13); c.drawString(x+30,by,tag)
    c.setStrokeColor(RULE); c.setLineWidth(1); c.line(x,by-12,x+c3,by-12)
    para(c,body,x,by-30,c3,f="Sans",s=11,lead=16,col=MUTE)
# Bottom strip — reproducibility (link+QR) and AI disclosure
sy=118; sh=118
card(c,MX,sy-sh,W-2*MX,sh,r=10,shadow=False)
# QR
qx=MX+22; qsz=94
image_fit(c,f"{A}/qr_code.png",qx,sy-sh+12,qsz,qsz)
link_rect(c,URLS["code"],qx,sy-sh+12,qsz,qsz)
# repro text
tx=qx+qsz+22
eyebrow(c,"REPRODUCIBILITY",tx,sy-26,col=CRIM,sz=9.5)
para(c,"Every number and figure is regenerated by one commented notebook — scan or open:",
     tx,sy-46,470,f="Sans",s=11.5,lead=16,col=INK)
link_text(c,URL_LABELS["code"],URLS["code"],tx,sy-84,f="MonoB",s=11,col=SLATE)
# divider
dvx=tx+520
c.setStrokeColor(RULE); c.setLineWidth(1); c.line(dvx,sy-18,dvx,sy-sh+18)
# AI disclosure
adx=dvx+26
eyebrow(c,"AI DISCLOSURE",adx,sy-26,col=CRIM,sz=9.5)
para(c,"An AI assistant helped scaffold code and copy-edit text. All figures were independently verified by the author against the source data; the analysis, interpretation and design are the author’s own.",
     adx,sy-46,W-MX-adx-22,f="Sans",s=11,lead=15.5,col=MUTE)
c.showPage()

# ---------------- 5. INSIGHTS ----------------
chrome(c,5)
header(c,"04","INSIGHTS FROM THE DATA","Insights from the data")
cards=[
 ("5.26 M  vs  3 953","THEFTS vs INTENTIONAL HOMICIDES · 2024",
  "Property crime is the volume of crime — about 1 330× more thefts than homicides. The offences people fear most are the rarest: volume is not gravity.",SLATE),
 ("+94% / +150%","SEXUAL VIOLENCE / RAPE · 2014→2024",
  "The fastest-rising records, on a fixed country basket. Eurostat ties part of it to better reporting — recorded crime measures the system’s response as much as the underlying reality.",CRIM),
 ("−20% → +21%","THEFT · PANDEMIC TROUGH then REBOUND",
  "A near round-trip: thefts fell ~20% to 2021, rebounded ~21% by 2024, then cooled 2% year-on-year — yet still far below 7.4 M in 2008. Shocks move property crime sharply but briefly.",SLATE),
 ("47× spread","THEFT RATE vs HOMICIDE RATE · BY COUNTRY",
  "Geography inverts reputation: Luxembourg records Europe’s highest theft rate yet its lowest homicide rate. Theft ranks track recording practice; homicide — the most comparable offence — puts the Baltics highest.",SLATE),
]
colw=(W-2*MX-40)/2; gut=40; ch=132; top=H-206
for i,(stat,lab,note,acc) in enumerate(cards):
    col=i%2; rowi=i//2
    x=MX+col*(colw+gut); y=top-rowi*(ch+22)
    card(c,x,y-ch,colw,ch,r=12)
    c.setFillColor(acc); c.roundRect(x,y-ch,6,ch,3,fill=1,stroke=0)
    c.setFillColor(acc); c.setFont("SansB",30); c.drawString(x+28,y-44,stat)
    tspace(c,lab,x+28,y-64,"MonoB",8.5,MUTE,gap=1.0)
    para(c,note,x+28,y-84,colw-52,f="Sans",s=11,lead=15.5,col=INK)
c.setFillColor(MUTE); c.setFont("Mono",9.5)
c.drawString(MX,82,"Also: corruption offences reached 82 947 in 2024 (+9.8% vs 2023) — the highest since 2017, incl. 9 207 bribery offences. A small but rising category.")
c.showPage()

# ---------- shared viz-slide layout ----------
def viz_slide(page, kicker, title, paras, chart, italic=None, italic_lines=3):
    chrome(c,page)
    eyebrow(c,kicker,MX,H-92)
    txtw=430
    ty=para(c,title,MX,H-146,txtw,f="SansB",s=29,lead=36,col=INK)
    ty-=18
    for p in paras:
        ty=para(c,p,MX,ty,txtw,f="Sans",s=13.5,lead=21,col=INK)
        ty-=8
    if italic:
        ty-=6
        c.setStrokeColor(CRIM); c.setLineWidth(2)
        c.line(MX,ty+6,MX,ty-18*(italic_lines-1)-8)
        para(c,italic,MX+16,ty,txtw-16,f="SerifI",s=12.5,lead=18,col=MUTE)
    cardx=MX+txtw+44; cardw=W-MX-cardx; cardy=96; cardh=H-56-96-30
    card(c,cardx,cardy,cardw,cardh,r=12)
    image_fit(c,chart,cardx+14,cardy+14,cardw-28,cardh-28,mask=None)
    return cardx,cardw,cardy,cardh

# ---------------- 6. VIZ 1 — COMPOSITION ----------------
viz_slide(6,"05 — DATA VISUALISATION 1 · MATPLOTLIB",
    "The volume of crime is property crime",
    ["Ranking every major offence by its 2024 count puts the debate in proportion. Theft alone — 5.26 million recorded offences — plus burglary make up the overwhelming majority of recorded crime in the EU-27.",
     "On a logarithmic scale the gap is stark: roughly 1 330 recorded thefts for every intentional homicide. The rarest offences are also the gravest — answering research question 1."],
    f"{A}/viz1_composition.png",
    italic="A log scale is used because the categories span more than three orders of magnitude.",
    italic_lines=2)
c.showPage()

# ---------------- 7. VIZ 2 — MAP + interactive ----------------
cardx,cardw,cardy,cardh = viz_slide(7,"06 — DATA VISUALISATION 2 · GEOGRAPHY",
    "The map of crime defies its reputation",
    ["Intentional homicide is the most internationally comparable offence — least sensitive to how each country records crime. Mapped per 100 000 in 2024, it puts the Baltics highest and much of the Mediterranean south (Italy, Spain) lowest, inverting the usual stereotype.",
     "Theft rate tells the opposite story — a 47× spread led by Luxembourg — but that ranking tracks recording practice, not danger. This answers research question 2: geography depends entirely on which offence you count."],
    f"{A}/viz2_map_homicide.png")
# interactive callout ribbon under the text
ry=150
c.setFillColor(CRIM); c.roundRect(MX,ry-58,430,58,8,fill=1,stroke=0)
tspace(c,"EXPLORE IT LIVE",MX+16,ry-22,"MonoB",8.5,HexColor("#FFFFFF"),gap=1.4)
c.setFillColor(HexColor("#FFFFFF")); c.setFont("Sans",10.5)
c.drawString(MX+16,ry-40,"Interactive choropleth · switch offence, hover, zoom")
# QR + link to the dashboard (over the ribbon, right side)
qsz=44
image_fit(c,f"{A}/qr_dashboard.png",MX+430-qsz-12,ry-58+7,qsz,qsz)
link_rect(c,URLS["dashboard"],MX,ry-58,430,58)
c.showPage()

# ---------------- 8. VIZ 3 — THEFT TREND ----------------
viz_slide(8,"07 — DATA VISUALISATION 3 · MATPLOTLIB",
    "Property crime dipped, then bounced back",
    ["Theft is the single largest offence, so its trend drives the headline. It had been falling for a decade when the 2020–21 lockdowns cut opportunity: recorded thefts fell about 20% to a 2021 trough.",
     "The reopening reversed most of it — a ~21% rebound by 2024, then a 2% cooling year-on-year. This answers research question 3: the pandemic was a sharp shock on a longer downward path (7.4 M in 2008 → 5.26 M today)."],
    f"{A}/viz3_theft_trend.png",
    italic="Recorded thefts respond to opportunity — mobility, retail footfall — as much as to policing.",
    italic_lines=2)
c.showPage()

# ---------------- 9. VIZ 4 — SEXUAL VIOLENCE ----------------
viz_slide(9,"08 — DATA VISUALISATION 4 · SEABORN",
    "Sexual violence: a decade of rising reports",
    ["Against a broadly stable picture for most offences, one category stands apart. Between 2014 and 2024, police-recorded sexual-violence offences rose 94%, and recorded rape 150% — on a fixed set of reporting countries, so the rise is not a coverage artefact.",
     "Eurostat cautions this partly reflects greater awareness and reporting, not incidence alone. This answers research question 4: recorded crime measures the system’s response as much as the underlying reality."],
    f"{A}/viz4_sexualviolence.png",
    italic="Same country basket at both endpoints (SV 27/27; rape 26/27, Italy absent in both years).",
    italic_lines=3)
c.showPage()

# ---------------- 10. RESULTS / CONCLUSIONS ----------------
chrome(c,10)
header(c,"09","RESULTS & CONCLUSIONS","Results & conclusions")
# left: the answer + four takeaways
lead_txt="One word, many trends: “crime” has no single direction. Whether EU crime is rising or falling depends entirely on which offence you count — and where."
ty=para(c,lead_txt,MX,H-198,560,f="SansB",s=18,lead=26,col=INK)
ty-=14
concl=[
 ("Volume ≠ gravity","Property crime dominates the count (5.26 M thefts); the gravest offence, homicide, is ~1 330× rarer."),
 ("Trends diverge","Theft is down over the decade with a COVID dip-and-rebound; sexual-violence reports are up 94%."),
 ("Reporting matters","Part of the sexual-violence rise reflects better reporting — the data measure the system, not only reality."),
 ("Geography ≠ reputation","Homicide is highest in the Baltics, not the south; theft rankings track recording practice, not danger."),
]
for t,b in concl:
    c.setFillColor(CRIM); c.setFont("SansB",12); c.drawString(MX,ty,"›")
    c.setFillColor(INK); c.setFont("SansB",12.5); c.drawString(MX+16,ty,t)
    ty=para(c,b,MX+16,ty-17,560-16,f="Sans",s=11.5,lead=16,col=MUTE)
    ty-=9
# right: deliverables card with clickable links + QR
dx=MX+620; dw=W-MX-dx; dyt=H-196; dh=360
card(c,dx,dyt-dh,dw,dh,r=12)
eyebrow(c,"EXPLORE & REPRODUCE",dx+24,dyt-30,col=CRIM,sz=9.5)
# dashboard
image_fit(c,f"{A}/qr_dashboard.png",dx+24,dyt-150,96,96)
link_rect(c,URLS["dashboard"],dx+24,dyt-150,96,96)
c.setFillColor(INK); c.setFont("SansB",13); c.drawString(dx+136,dyt-72,"Interactive dashboard")
para(c,"European map with an offence selector, trend and index panels.",dx+136,dyt-90,dw-136-24,f="Sans",s=10.5,lead=14,col=MUTE)
link_text(c,URL_LABELS["dashboard"],URLS["dashboard"],dx+136,dyt-134,f="MonoB",s=10,col=SLATE)
c.setStrokeColor(RULE); c.setLineWidth(1); c.line(dx+24,dyt-172,dx+dw-24,dyt-172)
# code
image_fit(c,f"{A}/qr_code.png",dx+24,dyt-300,96,96)
link_rect(c,URLS["code"],dx+24,dyt-300,96,96)
c.setFillColor(INK); c.setFont("SansB",13); c.drawString(dx+136,dyt-222,"Reproducible notebook")
para(c,"One commented notebook regenerates every figure and number in this deck.",dx+136,dyt-240,dw-136-24,f="Sans",s=10.5,lead=14,col=MUTE)
link_text(c,URL_LABELS["code"],URLS["code"],dx+136,dyt-284,f="MonoB",s=10,col=SLATE)
c.showPage()

# ---------------- 11. LICENCE ----------------
chrome(c,11)
header(c,"10","LICENCE","Licence")
ly=H-232
c.setStrokeColor(CRIM); c.setLineWidth(3); c.line(MX,ly+16,MX,ly-86)
para(c,"“Crime in Europe: one word, many trends” by "+STUDENT["name"],
     MX+24,ly,900,f="SansB",s=20,lead=28,col=INK)
yy=ly-44
yy=para(c,"is licensed under a Creative Commons Attribution 4.0 International License (CC BY 4.0), matching Eurostat’s own reuse terms.",
     MX+24,yy,900,f="Sans",s=15,lead=23,col=INK)
lic_url="https://creativecommons.org/licenses/by/4.0/"
c.setFillColor(SLATE); c.setFont("Mono",12); c.drawString(MX+24,yy-4,"creativecommons.org/licenses/by/4.0/")
link_rect(c,lic_url,MX+24,yy-8,sw("creativecommons.org/licenses/by/4.0/","Mono",12),18)
ay=240
card(c,MX,ay-96,W-2*MX,96,r=10,shadow=False)
eyebrow(c,"DATA ATTRIBUTION",MX+24,ay-28,col=CRIM,sz=9.5)
para(c,"Contains Eurostat data — Source: Eurostat (crim_off_cat), © European Union. Reused under the Eurostat reuse policy, which permits reproduction with acknowledgement of the source and indication of any modifications. EU-27 aggregates were reconstructed by the author by summing member-state values.",
     MX+24,ay-50,W-2*MX-48,f="Sans",s=12.5,lead=19,col=INK)
c.showPage()

c.save()
print("RAW PDF written:", OUT)
