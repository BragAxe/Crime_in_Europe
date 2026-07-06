#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble a clean, Colab-ready analysis.ipynb (no external font/geo deps)."""
import json, os

def md(*lines):  return {"cell_type":"markdown","metadata":{},"source":list(_join(lines))}
def code(*lines):return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":list(_join(lines))}
def _join(lines):
    text="\n".join(lines)
    # nbformat wants a list of lines each ending in \n (except last)
    parts=text.split("\n")
    return [p+"\n" for p in parts[:-1]]+[parts[-1]]

cells=[]

cells.append(md(
"# Crime in Europe — reproducible analysis",
"",
"**One word, many trends.** This notebook regenerates *every figure and number* used in the",
"companion pitch deck, straight from the official Eurostat export `crim_off_cat`.",
"",
"**Method in one line.** The raw export has **no EU aggregate row**, so all EU-27 totals are",
"reconstructed by summing the 27 member states; time comparisons use a **consistent country",
"basket**; cross-country geography uses **per-100 000 rates** (coverage-independent).",
"",
"### How to run (Google Colab)",
"1. `Runtime -> Run all`.",
"2. When prompted, upload `crim_off_cat_linear_2_0.csv` (the Eurostat SDMX-CSV export).",
"3. Every number printed here matches the deck; the four figures are regenerated below.",
))

cells.append(md("## 0 · Setup & data loading"))
cells.append(code(
"import os",
"import numpy as np",
"import pandas as pd",
"import matplotlib.pyplot as plt",
"import matplotlib.ticker as mticker",
"import seaborn as sns",
"",
"# Palette (identical to the deck)",
"INK='#1B1B25'; MUTE='#6C6C78'; GRID='#E8E4DB'; SLATE='#2C6E6A'",
"CRIMSON='#A6132A'; SAND='#C9C0AE'; GOLD='#C8772E'; FAINT='#9A958A'",
"plt.rcParams.update({'figure.dpi':120,'savefig.dpi':200,'axes.edgecolor':'#B9B3A6',",
"    'axes.linewidth':0.8,'font.size':11})",
"",
"CSV = 'crim_off_cat_linear_2_0.csv'",
"if not os.path.exists(CSV):",
"    try:",
"        from google.colab import files",
"        print('Upload the Eurostat export crim_off_cat_linear_2_0.csv ...')",
"        up = files.upload()",
"        CSV = next(iter(up))",
"    except Exception as e:",
"        raise FileNotFoundError('Place crim_off_cat_linear_2_0.csv next to this notebook, or upload it.') from e",
"",
"raw = pd.read_csv(CSV)",
"df = raw[['iccs','unit','geo','TIME_PERIOD','OBS_VALUE']].rename(",
"        columns={'TIME_PERIOD':'year','OBS_VALUE':'value'})",
"print('rows:', len(df), '| years:', df.year.min(), '-', df.year.max(),",
"      '| geos:', df.geo.nunique(), '| ICCS categories:', df.iccs.nunique())",
))

cells.append(md("## 1 · Constants — EU-27, geo codes, ICCS categories"))
cells.append(code(
"# EU-27 (post-Brexit). The export has no aggregate row, so we sum these.",
"EU27 = ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','EL','HU','IE',",
"        'IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE']",
"",
"# Eurostat geo code -> (name, ISO-3). Note: EL=Greece(GRC); UK reported sub-nationally.",
"GEO = {",
" 'AL':('Albania','ALB'),'AT':('Austria','AUT'),'BA':('Bosnia & Herz.','BIH'),",
" 'BE':('Belgium','BEL'),'BG':('Bulgaria','BGR'),'CH':('Switzerland','CHE'),",
" 'CY':('Cyprus','CYP'),'CZ':('Czechia','CZE'),'DE':('Germany','DEU'),",
" 'DK':('Denmark','DNK'),'EE':('Estonia','EST'),'EL':('Greece','GRC'),",
" 'ES':('Spain','ESP'),'FI':('Finland','FIN'),'FR':('France','FRA'),",
" 'HR':('Croatia','HRV'),'HU':('Hungary','HUN'),'IE':('Ireland','IRL'),",
" 'IS':('Iceland','ISL'),'IT':('Italy','ITA'),'LI':('Liechtenstein','LIE'),",
" 'LT':('Lithuania','LTU'),'LU':('Luxembourg','LUX'),'LV':('Latvia','LVA'),",
" 'ME':('Montenegro','MNE'),'MK':('North Macedonia','MKD'),'MT':('Malta','MLT'),",
" 'NL':('Netherlands','NLD'),'NO':('Norway','NOR'),'PL':('Poland','POL'),",
" 'PT':('Portugal','PRT'),'RO':('Romania','ROU'),'RS':('Serbia','SRB'),",
" 'SE':('Sweden','SWE'),'SI':('Slovenia','SVN'),'SK':('Slovakia','SVK'),",
" 'TR':('Turkiye','TUR'),'XK':('Kosovo','XKX')}",
"",
"ICCS = {'homicide':'ICCS0101','sexual_violence':'ICCS0301','rape':'ICCS03011',",
"        'robbery':'ICCS0401','burglary':'ICCS0501','theft':'ICCS0502',",
"        'corruption':'ICCS0703','bribery':'ICCS07031'}",
"NAME = {'homicide':'Intentional homicide','sexual_violence':'Sexual violence',",
"        'rape':'Rape','robbery':'Robbery','burglary':'Burglary','theft':'Theft',",
"        'corruption':'Corruption','bribery':'Bribery'}",
"",
"def series(code, unit='NR', geos=EU27):",
"    \"\"\"{year: (sum, n_countries, [present])} over a consistent geo set.\"\"\"",
"    sub = df[(df['iccs']==code)&(df['unit']==unit)&(df['geo'].isin(geos))]",
"    out={}",
"    for yr,g in sub.groupby('year'):",
"        gg=g[g['value'].notna()]",
"        out[int(yr)]=(float(gg['value'].sum()), int(len(gg)), sorted(gg['geo']))",
"    return out",
"",
"def eu_sum(code, year, unit='NR'):",
"    return series(code, unit).get(year,(np.nan,0,[]))",
))

cells.append(md(
"## 2 · Composition 2024 — the volume of crime, and how rare homicide is",
"",
"Answers RQ1. Theft dominates; intentional homicide is ~1 330× rarer.",
))
cells.append(code(
"order=['theft','burglary','sexual_violence','robbery','corruption','homicide']",
"rows=[]",
"for k in order:",
"    val,n,present=eu_sum(ICCS[k],2024)",
"    rows.append({'category':NAME[k],'value_2024':int(round(val)),'coverage':f'{n}/27'})",
"comp=pd.DataFrame(rows)",
"theft24=comp.loc[comp.category=='Theft','value_2024'].iloc[0]",
"hom24=comp.loc[comp.category=='Intentional homicide','value_2024'].iloc[0]",
"ratio=theft24/hom24",
"print(comp.to_string(index=False))",
"print(f'\\nTheft:homicide ratio = {ratio:.1f}x  (~{round(ratio,-1):.0f}x)')",
"",
"# --- figure: horizontal log bar ---",
"cc=comp.sort_values('value_2024')",
"colors=[CRIMSON if c=='Intentional homicide' else SLATE for c in cc.category]",
"fig,ax=plt.subplots(figsize=(9,4.6))",
"ax.barh(cc.category,cc.value_2024,color=colors,height=0.62,zorder=3)",
"ax.set_xscale('log'); ax.set_xlim(2e3,1e7)",
"ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f'{int(x):,}'.replace(',',' ')))",
"ax.grid(axis='x',color=GRID,zorder=0); ax.set_axisbelow(True)",
"for s in ['top','right','left']: ax.spines[s].set_visible(False)",
"for c,v in zip(cc.category,cc.value_2024):",
"    ax.text(v*1.15,c,f'{v:,}'.replace(',',' '),va='center',fontsize=9,color=INK)",
"ax.annotate(f'~ {round(ratio,-1):.0f}x more thefts than homicides',",
"    xy=(hom24,'Intentional homicide'),xytext=(theft24*0.9,'Robbery'),",
"    fontsize=12,fontweight='bold',color=CRIMSON,ha='right',",
"    arrowprops=dict(arrowstyle='->',color=CRIMSON,lw=1.4))",
"ax.set_title('EU-27 recorded offences by category, 2024 (log scale)',",
"    loc='left',fontsize=13,fontweight='bold',color=INK)",
"plt.tight_layout(); plt.savefig('fig1_composition.png'); plt.show()",
))

cells.append(md(
"## 3 · Theft trend 2008–2024 — pandemic dip and rebound",
"",
"Answers RQ3. A ~20% COVID trough, a ~21% rebound, then −2% YoY — on a long secular decline.",
))
cells.append(code(
"th=series(ICCS['theft'])",
"tt=pd.DataFrame([{'year':y,'theft':int(round(v))} for y,(v,n,_) in sorted(th.items())])",
"v=lambda yr:int(tt.loc[tt.year==yr,'theft'].iloc[0])",
"v19,v21,v23,v24=v(2019),v(2021),v(2023),v(2024)",
"dip=(v21/v19-1)*100; reb=(v24/v21-1)*100; yoy=(v24/v23-1)*100",
"print(f'2008={v(2008):,}  2019={v19:,}  2021(trough)={v21:,}  2024={v24:,}')",
"print(f'dip 2021 vs 2019 = {dip:+.1f}%   rebound 2024 vs 2021 = {reb:+.1f}%   YoY = {yoy:+.1f}%')",
"",
"fig,ax=plt.subplots(figsize=(9,4.6))",
"ax.axvspan(2020,2021.4,color=SAND,alpha=0.35,zorder=0)",
"ax.plot(tt.year,tt.theft,color=SLATE,lw=2.6,marker='o',ms=4,zorder=3)",
"ax.scatter([2021],[v21],color=CRIMSON,zorder=4,s=40)",
"ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y,_:f'{y/1e6:.0f}M'))",
"ax.grid(axis='y',color=GRID); ax.set_axisbelow(True)",
"for s in ['top','right']: ax.spines[s].set_visible(False)",
"ax.annotate(f'trough {dip:+.0f}%',(2021,v21),xytext=(2021.4,v21-5.5e5),color=CRIMSON,fontsize=10,fontweight='bold')",
"ax.annotate(f'rebound {reb:+.0f}%',(2024,v24),xytext=(2021.7,v24+2e5),color=SLATE,fontsize=10,fontweight='bold')",
"ax.set_title('Recorded thefts, EU-27, 2008–2024',loc='left',fontsize=13,fontweight='bold',color=INK)",
"plt.tight_layout(); plt.savefig('fig3_theft_trend.png'); plt.show()",
))

cells.append(md(
"## 4 · Sexual violence & rape — a decade of rising reports (consistent basket)",
"",
"Answers RQ4. +94% / +150% on a fixed set of reporting countries, so not a coverage artefact.",
))
cells.append(code(
"idx_rows=[]",
"for k in ['sexual_violence','rape']:",
"    a14,na14,ca14=eu_sum(ICCS[k],2014); a24,na24,ca24=eu_sum(ICCS[k],2024)",
"    idx_rows.append({'category':NAME[k],'v2014':int(round(a14)),'v2024':int(round(a24)),",
"        'coverage_2024':f'{na24}/27','same_basket':ca14==ca24,",
"        'growth_%':round((a24/a14-1)*100,1),'index_2024':round(a24/a14*100,1)})",
"idx=pd.DataFrame(idx_rows); print(idx.to_string(index=False))",
"",
"fig,ax=plt.subplots(figsize=(7.4,4.6))",
"cats=idx.category.tolist(); x=np.arange(len(cats)); w=0.36",
"ax.bar(x-w/2,[100,100],w,label='2014 = 100',color=SAND,zorder=3)",
"ax.bar(x+w/2,idx.index_2024,w,label='2024',color=CRIMSON,zorder=3)",
"for xi,val,g in zip(x,idx.index_2024,idx['growth_%']):",
"    ax.text(xi+w/2,val+4,f'+{g:.0f}%',ha='center',fontsize=11,fontweight='bold',color=CRIMSON)",
"ax.set_xticks(x); ax.set_xticklabels(cats); ax.set_ylabel('Index (2014 = 100)')",
"ax.grid(axis='y',color=GRID); ax.set_axisbelow(True)",
"for s in ['top','right']: ax.spines[s].set_visible(False)",
"ax.legend(frameon=False,loc='upper left')",
"ax.set_title('Recorded sexual violence & rape, EU-27, 2014 vs 2024',loc='left',fontsize=13,fontweight='bold',color=INK)",
"ax.text(0,-28,'Same country basket at both endpoints (SV 27/27; rape 26/27, Italy absent in both).',",
"    fontsize=8.5,color=MUTE)",
"plt.tight_layout(); plt.savefig('fig4_sexual_violence.png'); plt.show()",
))

cells.append(md(
"## 5 · Geography — homicide rate vs theft rate (per 100 000)",
"",
"Answers RQ2. Homicide (the most comparable offence) is highest in the Baltics and lowest in",
"much of the south — inverting the stereotype. Theft rate inverts *that* (Luxembourg highest),",
"because theft rankings track recording practice, not danger. The deck renders this as a map;",
"here it is a ranked view plus the key spans.",
))
cells.append(code(
"rate_off=['homicide','theft','burglary','robbery']",
"rate=df[(df['unit']=='P_HTHAB')&(df['year']==2024)&",
"        (df['iccs'].isin([ICCS[k] for k in rate_off]))&(df['value'].notna())].copy()",
"inv={ICCS[k]:k for k in rate_off}; rate['offence']=rate['iccs'].map(inv)",
"wide=rate.pivot_table(index='geo',columns='offence',values='value',aggfunc='first').reset_index()",
"wide=wide[wide['geo'].isin(GEO)]",
"wide['country']=wide['geo'].map(lambda g:GEO[g][0])",
"hom=wide[['country','homicide']].dropna().sort_values('homicide',ascending=False)",
"th=wide[['country','theft']].dropna().sort_values('theft',ascending=False)",
"print(f\"homicide rate: {hom.homicide.max():.2f} ({hom.iloc[0].country}) -> {hom.homicide.min():.2f} ({hom.iloc[-1].country})\")",
"print(f\"theft rate:    {th.theft.max():.0f} ({th.iloc[0].country}) -> {th.theft.min():.0f} ({th.iloc[-1].country}) = {th.theft.max()/th.theft.min():.0f}x span\")",
"print(f\"Luxembourg: theft-rate rank #{list(th.country).index('Luxembourg')+1}, homicide-rate rank #{list(hom.country).index('Luxembourg')+1} of {len(hom)}\")",
"",
"baltics={'Lithuania','Latvia','Estonia'}",
"colors=[CRIMSON if c in baltics else SLATE for c in hom.country]",
"fig,ax=plt.subplots(figsize=(8.4,7.2))",
"ax.barh(hom.country[::-1],hom.homicide[::-1],color=colors[::-1],height=0.7,zorder=3)",
"ax.grid(axis='x',color=GRID); ax.set_axisbelow(True)",
"for s in ['top','right','left']: ax.spines[s].set_visible(False)",
"ax.set_xlabel('Intentional homicide, per 100 000 (2024)')",
"ax.set_title('Homicide is highest in the Baltics — not the south',loc='left',fontsize=13,fontweight='bold',color=INK)",
"plt.tight_layout(); plt.savefig('fig2_homicide_rate.png'); plt.show()",
))

cells.append(md("## 6 · Corruption context"))
cells.append(code(
"co=series(ICCS['corruption'])",
"cser=pd.DataFrame([{'year':y,'corruption':int(round(v))} for y,(v,n,_) in sorted(co.items())])",
"c24=int(cser.loc[cser.year==2024,'corruption'].iloc[0]); c23=int(cser.loc[cser.year==2023,'corruption'].iloc[0])",
"brib=int(round(eu_sum(ICCS['bribery'],2024)[0]))",
"print(f'corruption 2024 = {c24:,}  (+{(c24/c23-1)*100:.1f}% vs 2023) — highest since 2017')",
"print(f'bribery 2024    = {brib:,}')",
"print('Note: corruption has no 2014 EU-27 baseline (0/27 reported in 2014), so it is framed as \"highest since 2017\", never 2014-indexed.')",
))

cells.append(md(
"## 7 · Verified figure sheet",
"",
"These are the exact numbers used in the deck.",
))
cells.append(code(
"print('=== VERIFIED FIGURE SHEET (EU-27, real crim_off_cat) ===')",
"print(f'theft_2024           = {theft24:,}')",
"print(f'homicide_2024        = {hom24:,}')",
"print(f'theft:homicide       = {ratio:.1f}x (~{round(ratio,-1):.0f}x)')",
"for k in ['burglary','robbery','sexual_violence']:",
"    val,n,_=eu_sum(ICCS[k],2024); print(f'{k:20s} = {int(round(val)):,}  ({n}/27)')",
"print(f'theft round-trip     : 2019={v19:,} -> 2021={v21:,} ({dip:+.1f}%) -> 2024={v24:,} ({reb:+.1f}%), YoY {yoy:+.1f}%')",
"for _,r in idx.iterrows():",
"    print(f\"{r['category']:16s} 2014={r['v2014']:,} -> 2024={r['v2024']:,} | +{r['growth_%']:.0f}% | same_basket={r['same_basket']}\")",
"print(f'corruption_2024      = {c24:,} (+{(c24/c23-1)*100:.1f}%); bribery_2024 = {brib:,}')",
))

cells.append(md(
"---",
"*Data: Eurostat (crim_off_cat), © European Union — reused under the Eurostat reuse policy",
"(≈ CC BY 4.0). EU-27 aggregates reconstructed by summing member states. This notebook is the",
"reproducibility companion to the pitch deck; the deck's exact styled figures are produced by",
"the accompanying `prepare_data.py` + `make_charts_v2.py` scripts.*",
))

nb={"cells":cells,
    "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                "language_info":{"name":"python","version":"3.11"},
                "colab":{"provenance":[]}},
    "nbformat":4,"nbformat_minor":5}

_HERE=os.path.dirname(os.path.abspath(__file__))
_ROOT=os.path.dirname(_HERE) if os.path.basename(_HERE)=="scripts" else _HERE
_DST=os.path.join(_ROOT,"analysis.ipynb")
with open(_DST,"w") as f:
    json.dump(nb,f,indent=1)
print("wrote",_DST,"with",len(cells),"cells")
