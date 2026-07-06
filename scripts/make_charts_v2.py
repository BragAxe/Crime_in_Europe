#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the four editorial figures for the 'Crime in Europe' v2 deck.
Tool A (this file): Python / Matplotlib + Seaborn -> static vector-quality PNGs.
Reads the clean tables written by prepare_data.py.  Palette = v1 (unchanged)."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyBboxPatch, Circle
import matplotlib.patheffects as pe
import seaborn as sns
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE)=="scripts" else HERE
DATA = os.path.join(ROOT, "data")
OUT  = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

# ---- Fonts (Liberation + DejaVu, as v1) ----
F = {
 "sans":  "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
 "sansb": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
 "mono":  "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
 "monob": "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
}
for p in F.values(): fm.fontManager.addfont(p)
SANS  = fm.FontProperties(fname=F["sans"])
SANSB = fm.FontProperties(fname=F["sansb"])
MONO  = fm.FontProperties(fname=F["mono"])
MONOB = fm.FontProperties(fname=F["monob"])
plt.rcParams["font.family"] = SANS.get_name()
plt.rcParams["svg.fonttype"] = "none"

# ---- Palette (v1) ----
INK="#1B1B25"; MUTE="#6C6C78"; PAPER="#FFFFFF"; GRID="#E8E4DB"
SLATE="#2C6E6A"; SLATE_D="#1F5350"; CRIMSON="#A6132A"; SAND="#C9C0AE"
GOLD="#C8772E"; FAINT="#9A958A"

def strip_png(path):
    im = Image.open(path); data=list(im.getdata())
    clean=Image.new(im.mode, im.size); clean.putdata(data)
    clean.save(path, "PNG")

def sp(n): return f"{int(round(n)):,}".replace(",", " ")  # space sep (Eurostat style)

# =====================================================================
# VIZ 1 — Matplotlib: composition of recorded offences, EU 2024 (log)
#         (v1 improved: enlarged 1330x annotation)
# =====================================================================
comp = pd.read_csv(f"{DATA}/composition_2024.csv")
comp = comp.sort_values("value_2024")           # ascending -> homicide at bottom
cats = comp["category"].tolist(); vals = comp["value_2024"].tolist()
colors = [CRIMSON if c=="Intentional homicide" else SLATE for c in cats]

def logbar(figsize, cover=False):
    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    if cover:
        fig.patch.set_facecolor("none"); ax.set_facecolor("none")
    else:
        fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    y = np.arange(len(cats))
    ax.barh(y, vals, color=colors, height=0.62, zorder=3)
    ax.set_xscale("log"); ax.set_xlim(1e3, 2.2e7)
    for s in ["top","right","left"]: ax.spines[s].set_visible(False)
    ax.set_yticks(y)
    ax.set_yticklabels(cats, fontproperties=SANSB, fontsize=11, color=INK)
    ax.tick_params(axis="y", length=0)
    if cover:
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_xticks([]); ax.minorticks_off(); ax.tick_params(which="both",length=0)
        ax.xaxis.grid(False)
        for i,v in enumerate(vals):
            ax.text(v*1.2, i, sp(v), va="center", ha="left",
                    fontproperties=MONOB, fontsize=9.2,
                    color=CRIMSON if cats[i]=="Intentional homicide" else MUTE)
        fig.subplots_adjust(left=0.30, right=0.96, top=0.99, bottom=0.02)
        return fig, ax
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="x", colors=MUTE, length=0, labelsize=9)
    ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    def logfmt(x,_):
        if x>=1e6: return f"{x/1e6:.0f}M"
        if x>=1e3: return f"{x/1e3:.0f}K"
        return f"{x:.0f}"
    ax.xaxis.set_major_formatter(FuncFormatter(logfmt))
    for i,v in enumerate(vals):
        ax.text(v*1.18, i, sp(v), va="center", ha="left",
                fontproperties=MONOB, fontsize=10,
                color=CRIMSON if cats[i]=="Intentional homicide" else INK)
    ax.set_xlabel("Number of police-recorded offences  ·  logarithmic scale",
                  fontproperties=SANS, fontsize=9, color=MUTE, labelpad=8)
    return fig, ax

# main viz1 with ENLARGED annotation
fig, ax = logbar((7.8, 5.2))
hom_i = cats.index("Intentional homicide")
ax.annotate("", xy=(3_953*1.5, hom_i), xytext=(1.55e5, hom_i+0.75),
            arrowprops=dict(arrowstyle="-", color=CRIMSON, lw=1.2,
                            connectionstyle="arc3,rad=-0.25"))
ax.text(1.65e5, hom_i+0.95, "\u2248 1 330\u00d7 more thefts\nthan homicides",
        fontproperties=SANSB, fontsize=12.5, color=CRIMSON, va="center", ha="left")
fig.subplots_adjust(left=0.225, right=0.965, top=0.965, bottom=0.115)
p1=f"{OUT}/viz1_composition.png"
fig.savefig(p1, dpi=300, facecolor=PAPER); plt.close(fig); strip_png(p1)
print("saved", p1)

# cover version
fig, ax = logbar((6.6, 3.4), cover=True)
pc=f"{OUT}/cover_chart.png"
fig.savefig(pc, dpi=300, transparent=True); plt.close(fig); strip_png(pc)
print("saved", pc)

# =====================================================================
# VIZ 2 — Tile-grid choropleth of Europe: homicide rate /100k, 2024
#         (NEW: geographic component; static twin of the interactive map)
# =====================================================================
hm = pd.read_csv(f"{DATA}/homicide_rate_2024.csv").set_index("geo")
rate = hm["homicide"].to_dict()

# European tile grid (row 0 = north). Hand-placed, geography-approximate.
GRID_POS = {
 "IS":(0,0),                          "FI":(0,7),
 "NO":(1,5),"SE":(1,6),               "EE":(1,8),
 "IE":(2,1),            "DK":(2,5),    "LV":(2,8),
 "NL":(3,4),"DE":(3,5),"PL":(3,7),    "LT":(3,8),
 "PT":(4,1),"ES":(4,2),"FR":(4,3),"BE":(4,4),"LU":(4,5),"CZ":(4,6),"SK":(4,7),
 "CH":(5,4),"LI":(5,5),"AT":(5,6),"HU":(5,7),"RO":(5,8),
 "IT":(6,3),"SI":(6,5),"HR":(6,6),"RS":(6,7),"BG":(6,8),
 "MT":(7,3),"BA":(7,6),"ME":(7,7),"MK":(7,8),
 "AL":(8,7),"XK":(8,8),"EL":(8,9),"CY":(8,11),"TR":(8,10),
}
# sequential light -> CRIMSON (homicide theme)
cmap = LinearSegmentedColormap.from_list("hom", ["#F7EDE9","#E7A8A0","#C6504E","#A6132A","#6E0C1C"])
vmax = max(rate.values()); vmin = min(rate.values())
norm = Normalize(vmin=0, vmax=vmax)

rows = max(r for r,_ in GRID_POS.values())+1
cols = max(c for _,c in GRID_POS.values())+1
fig, ax = plt.subplots(figsize=(8.2, 5.6), dpi=300)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
cell=1.0; pad=0.08
HI = {"LT","LV","EE"}   # Baltic outlier cluster to ring
for geo,(r,cc) in GRID_POS.items():
    x=cc; y=rows-1-r
    val=rate.get(geo, np.nan)
    face = cmap(norm(val)) if geo in rate else "#EFEFEA"
    box=FancyBboxPatch((x+pad, y+pad), cell-2*pad, cell-2*pad,
                       boxstyle="round,pad=0.0,rounding_size=0.10",
                       linewidth=0, facecolor=face, zorder=2)
    ax.add_patch(box)
    # text colour: white on dark
    lum = 0 if geo not in rate else norm(val)
    tcol = "white" if (geo in rate and norm(val)>0.55) else INK
    ax.text(x+cell/2, y+cell/2+0.10, geo, ha="center", va="center",
            fontproperties=MONOB, fontsize=10.5, color=tcol, zorder=4)
    if geo in rate:
        ax.text(x+cell/2, y+cell/2-0.23, f"{val:.1f}", ha="center", va="center",
                fontproperties=MONO, fontsize=8.2, color=tcol, zorder=4)
# ring the Baltic outliers
for geo in HI:
    r,cc=GRID_POS[geo]; x=cc; y=rows-1-r
    ax.add_patch(Circle((x+cell/2,y+cell/2), 0.62, fill=False,
                        edgecolor=INK, lw=1.4, zorder=5))
# outlier callout — Baltics (ringed), label to the right of the cluster
lv_x, lv_y = GRID_POS["LV"][1], rows-1-GRID_POS["LV"][0]
ax.annotate("Baltics — highest\nrates in Europe",
            xy=(lv_x+0.62, lv_y+0.5), xytext=(lv_x+1.7, lv_y+0.9),
            fontproperties=SANSB, fontsize=10.5, color=INK, va="center", ha="left",
            arrowprops=dict(arrowstyle="-", color=INK, lw=1.1,
                            connectionstyle="arc3,rad=-0.2"))
# low-rate note bottom-centre (IT & LU are lowest, far apart -> text only)
ax.text(4.9, -0.7,
        "Lowest recorded rates: Italy 0.6, Luxembourg 0.3 \u2014 the reverse of the\n"
        "\u2018dangerous South\u2019 stereotype; homicide is the most comparable offence.",
        fontproperties=SANS, fontsize=8.8, color=MUTE, ha="center", va="top")

ax.set_xlim(-0.3, cols+0.3); ax.set_ylim(-1.4, rows+0.5)
ax.set_aspect("equal"); ax.axis("off")

# colourbar
import matplotlib.cm as cm
sm=cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
cax=fig.add_axes([0.14, 0.085, 0.34, 0.028])
cb=fig.colorbar(sm, cax=cax, orientation="horizontal")
cb.outline.set_visible(False)
cb.set_ticks([0,1,2,vmax])
cb.ax.tick_params(labelsize=8, length=0, colors=MUTE)
for t in cb.ax.get_xticklabels(): t.set_fontproperties(MONO)
cb.set_label("Intentional homicides per 100 000 inhabitants · 2024",
             fontproperties=SANS, fontsize=9, color=MUTE, labelpad=6)
fig.subplots_adjust(left=0.02, right=0.98, top=0.99, bottom=0.02)
p2=f"{OUT}/viz2_map_homicide.png"
fig.savefig(p2, dpi=300, facecolor=PAPER); plt.close(fig); strip_png(p2)
print("saved", p2)

# =====================================================================
# VIZ 3 — Matplotlib: theft time series 2008-2024, pandemic dip/rebound
#         (NEW: trend analysis)
# =====================================================================
tt = pd.read_csv(f"{DATA}/theft_trend.csv")
yrs = tt["year"].values; th = tt["theft"].values/1e6
v19=tt.loc[tt.year==2019,"theft"].iloc[0]/1e6
v21=tt.loc[tt.year==2021,"theft"].iloc[0]/1e6
v24=tt.loc[tt.year==2024,"theft"].iloc[0]/1e6

fig, ax = plt.subplots(figsize=(7.8, 5.2), dpi=300)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
# pandemic band
ax.axvspan(2020, 2021.35, color="#F2ECE0", zorder=0)
ax.text(2020.67, 7.15, "COVID-19", ha="center", fontproperties=MONOB,
        fontsize=8.5, color=GOLD)
ax.plot(yrs, th, color=SLATE, lw=2.4, zorder=3, solid_capstyle="round")
ax.scatter(yrs, th, s=16, color=SLATE, zorder=4)
# highlight key points
for yr,val,col in [(2019,v19,MUTE),(2021,v21,CRIMSON),(2024,v24,SLATE_D)]:
    ax.scatter([yr],[val], s=64, color=col, zorder=5, edgecolor="white", lw=1.2)
ax.set_ylim(3.8, 7.7)
ax.set_xlim(2007.4, 2024.6)
for s in ["top","right"]: ax.spines[s].set_visible(False)
ax.spines["left"].set_color(GRID); ax.spines["bottom"].set_color(GRID)
ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
ax.set_xticks(range(2008,2025,2))
ax.tick_params(colors=MUTE, length=0, labelsize=9)
for t in ax.get_xticklabels()+ax.get_yticklabels(): t.set_fontproperties(MONO)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_: f"{x:.0f}M"))
ax.set_ylabel("Police-recorded thefts · EU-27", fontproperties=SANS,
              fontsize=9.5, color=MUTE)
# annotations
ax.annotate(f"2019\n{v19:.2f}M", xy=(2019,v19), xytext=(2016.3, 6.35),
            fontproperties=SANS, fontsize=9, color=MUTE, ha="center",
            arrowprops=dict(arrowstyle="-", color=MUTE, lw=0.9))
ax.annotate("pandemic trough\n\u221220% vs 2019", xy=(2021,v21),
            xytext=(2021.5, 4.15), fontproperties=SANSB, fontsize=10.5,
            color=CRIMSON, ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color=CRIMSON, lw=1.1,
                            connectionstyle="arc3,rad=0.25"))
ax.annotate(f"2024 rebound\n+21% vs trough,\nthen \u22122% YoY", xy=(2024,v24),
            xytext=(2022.0, 6.6), fontproperties=SANSB, fontsize=10.5,
            color=SLATE_D, ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color=SLATE_D, lw=1.1,
                            connectionstyle="arc3,rad=-0.2"))
fig.subplots_adjust(left=0.11, right=0.965, top=0.955, bottom=0.09)
p3=f"{OUT}/viz3_theft_trend.png"
fig.savefig(p3, dpi=300, facecolor=PAPER); plt.close(fig); strip_png(p3)
print("saved", p3)

# =====================================================================
# VIZ 4 — Seaborn: sexual violence & rape indexed 2014=100 -> 2024
#         (v1 improved: coverage note + reporting caveat)
# =====================================================================
idx = pd.read_csv(f"{DATA}/sexual_violence_index.csv")
sns.set_style("white")
labels=["Sexual\nviolence","Rape"]
idx2014=[100,100]
idx2024=[idx.loc[idx.key=='sexual_violence','index_2024'].iloc[0],
         idx.loc[idx.key=='rape','index_2024'].iloc[0]]
growth=[f"+{idx.loc[idx.key=='sexual_violence','growth_pct'].iloc[0]:.0f}%",
        f"+{idx.loc[idx.key=='rape','growth_pct'].iloc[0]:.0f}%"]

fig, ax = plt.subplots(figsize=(7.8, 5.2), dpi=300)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
x=np.arange(len(labels)); w=0.34
b1=ax.bar(x-w/2, idx2014, w, color=SAND, zorder=3, label="2014 (index = 100)")
b2=ax.bar(x+w/2, idx2024, w, color=CRIMSON, zorder=3, label="2024")
sns.despine(ax=ax, left=True)
ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
ax.set_ylim(0, 300)
ax.set_xticks(x); ax.set_xticklabels(labels, fontproperties=SANSB, fontsize=12, color=INK)
ax.tick_params(axis="y", colors=MUTE, length=0, labelsize=9)
ax.tick_params(axis="x", length=0)
for t in ax.get_yticklabels(): t.set_fontproperties(MONO)
ax.set_ylabel("Police-recorded offences, EU-27  (2014 = 100)",
              fontproperties=SANS, fontsize=9.5, color=MUTE)
for rect in list(b1):
    ax.text(rect.get_x()+rect.get_width()/2, rect.get_height()+5, "100",
            ha="center", fontproperties=MONO, fontsize=9, color=MUTE)
for rect,g,v in zip(b2, growth, idx2024):
    ax.text(rect.get_x()+rect.get_width()/2, v+5, f"{v:.0f}",
            ha="center", fontproperties=MONOB, fontsize=10, color=CRIMSON)
    ax.annotate(g, xy=(rect.get_x()+rect.get_width()/2, v+24),
                ha="center", fontproperties=SANSB, fontsize=14, color=CRIMSON)
leg=ax.legend(loc="upper left", frameon=False, prop=SANS, fontsize=9)
# reporting caveat band inside plot
ax.text(0.985, 0.055,
        "Same country basket at both endpoints (SV 27/27; rape 26/27, Italy n/a).\n"
        "Eurostat: partly improved reporting & awareness, not incidence alone.",
        transform=ax.transAxes, ha="right", va="bottom",
        fontproperties=SANS, fontsize=8.3, color=MUTE,
        bbox=dict(boxstyle="round,pad=0.5", fc="#FBF8F1", ec=GRID, lw=0.8))
fig.subplots_adjust(left=0.10, right=0.97, top=0.95, bottom=0.10)
p4=f"{OUT}/viz4_sexualviolence.png"
fig.savefig(p4, dpi=300, facecolor=PAPER); plt.close(fig); strip_png(p4)
print("saved", p4)
print("DONE")
