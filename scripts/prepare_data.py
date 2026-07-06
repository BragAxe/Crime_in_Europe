#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_data.py  —  Single source of truth for the "Crime in Europe" v2 deck.

Reads the real Eurostat SDMX-CSV export (crim_off_cat) and derives every
figure used in the deck, the interactive dashboard and the notebook.

Key methodological choices (documented in the deck's About/Methodology):
  * The raw export contains NO EU aggregate row -> the EU-27 total is
    reconstructed by summing the 27 member states for each category/year.
  * Comparisons over time use a CONSISTENT country basket: for indexed
    growth (2014->2024) we verify the same countries are present at both
    endpoints, so the % change is not a coverage artefact.
  * Cross-country geography uses the per-100k rate (P_HTHAB), which is
    population-normalised and coverage-independent per country.

Outputs -> ./data/*.csv
"""
import os
import pandas as pd
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE)=="scripts" else _HERE
SRC = os.environ.get("CRIM_CSV", "/mnt/user-data/uploads/crim_off_cat_linear_2_0.csv")
if not os.path.exists(SRC):
    _c = os.path.join(_ROOT, "data", "crim_off_cat_linear_2_0.csv")
    if os.path.exists(_c): SRC = _c
OUT = os.path.join(_ROOT, "data")
os.makedirs(OUT, exist_ok=True)

# ---- EU-27 (post-Brexit) --------------------------------------------------
EU27 = ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','EL','HU','IE',
        'IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE']

# ---- Eurostat geo code -> (English name, ISO-3166 alpha-3) -----------------
# Eurostat uses EL for Greece (GRC) and UK is reported at sub-national level.
GEO = {
 'AL':('Albania','ALB'),'AT':('Austria','AUT'),'BA':('Bosnia & Herz.','BIH'),
 'BE':('Belgium','BEL'),'BG':('Bulgaria','BGR'),'CH':('Switzerland','CHE'),
 'CY':('Cyprus','CYP'),'CZ':('Czechia','CZE'),'DE':('Germany','DEU'),
 'DK':('Denmark','DNK'),'EE':('Estonia','EST'),'EL':('Greece','GRC'),
 'ES':('Spain','ESP'),'FI':('Finland','FIN'),'FR':('France','FRA'),
 'HR':('Croatia','HRV'),'HU':('Hungary','HUN'),'IE':('Ireland','IRL'),
 'IS':('Iceland','ISL'),'IT':('Italy','ITA'),'LI':('Liechtenstein','LIE'),
 'LT':('Lithuania','LTU'),'LU':('Luxembourg','LUX'),'LV':('Latvia','LVA'),
 'ME':('Montenegro','MNE'),'MK':('North Macedonia','MKD'),'MT':('Malta','MLT'),
 'NL':('Netherlands','NLD'),'NO':('Norway','NOR'),'PL':('Poland','POL'),
 'PT':('Portugal','PRT'),'RO':('Romania','ROU'),'RS':('Serbia','SRB'),
 'SE':('Sweden','SWE'),'SI':('Slovenia','SVN'),'SK':('Slovakia','SVK'),
 'TR':('Turkiye','TUR'),'XK':('Kosovo','XKX'),
}

# ICCS codes we use
ICCS = {
 'homicide':'ICCS0101','sexual_violence':'ICCS0301','rape':'ICCS03011',
 'robbery':'ICCS0401','burglary':'ICCS0501','theft':'ICCS0502',
 'corruption':'ICCS0703','bribery':'ICCS07031',
}
NAME = {'homicide':'Intentional homicide','sexual_violence':'Sexual violence',
        'rape':'Rape','robbery':'Robbery','burglary':'Burglary','theft':'Theft',
        'corruption':'Corruption','bribery':'Bribery'}

# ===========================================================================
df = pd.read_csv(SRC)
df = df[['iccs','unit','geo','TIME_PERIOD','OBS_VALUE']].rename(
        columns={'TIME_PERIOD':'year','OBS_VALUE':'value'})

def series(code, unit='NR', geos=EU27):
    """Return {year: (sum_or_val, n_countries, [present_geos])} for a category."""
    sub = df[(df['iccs']==code)&(df['unit']==unit)&(df['geo'].isin(geos))]
    out = {}
    for yr, g in sub.groupby('year'):
        gg = g[g['value'].notna()]
        out[int(yr)] = (float(gg['value'].sum()), int(len(gg)), sorted(gg['geo']))
    return out

def eu_sum(code, year, unit='NR'):
    s = series(code, unit)
    return s.get(year, (np.nan,0,[]))

# ---- 1) COMPOSITION 2024 (log-bar) ----------------------------------------
comp_order = ['theft','burglary','sexual_violence','robbery','corruption','homicide']
rows = []
for k in comp_order:
    val, n, present = eu_sum(ICCS[k], 2024)
    missing = [g for g in EU27 if g not in present]
    rows.append({'key':k,'category':NAME[k],'value_2024':int(round(val)),
                 'countries':n,'missing':';'.join(missing)})
comp = pd.DataFrame(rows)
comp.to_csv(f"{OUT}/composition_2024.csv", index=False)

theft24 = int(comp.loc[comp.key=='theft','value_2024'].iloc[0])
hom24   = int(comp.loc[comp.key=='homicide','value_2024'].iloc[0])
ratio   = theft24 / hom24

# ---- 2) THEFT TREND 2008-2024 (pandemic dip/rebound) ----------------------
th = series(ICCS['theft'])
tt = pd.DataFrame([{'year':y,'theft':int(round(v)),'countries':n}
                   for y,(v,n,_) in sorted(th.items())])
base19 = tt.loc[tt.year==2019,'theft'].iloc[0]
tt['index_2019'] = (tt['theft']/base19*100).round(1)
tt.to_csv(f"{OUT}/theft_trend.csv", index=False)
v19 = int(tt.loc[tt.year==2019,'theft'].iloc[0])
v21 = int(tt.loc[tt.year==2021,'theft'].iloc[0])
v23 = int(tt.loc[tt.year==2023,'theft'].iloc[0])
v24 = int(tt.loc[tt.year==2024,'theft'].iloc[0])
dip = (v21/v19-1)*100
reb = (v24/v21-1)*100
yoy = (v24/v23-1)*100

# ---- 3) SEXUAL VIOLENCE / RAPE INDEX 2014=100 -----------------------------
idx_rows = []
for k in ['sexual_violence','rape']:
    v14,n14,c14 = eu_sum(ICCS[k],2014)
    v24k,n24,c24 = eu_sum(ICCS[k],2024)
    idx_rows.append({'key':k,'category':NAME[k],
                     'v2014':int(round(v14)),'v2024':int(round(v24k)),
                     'n2014':n14,'n2024':n24,
                     'same_basket': c14==c24,
                     'missing': ';'.join([g for g in EU27 if g not in c24]),
                     'index_2024': round(v24k/v14*100,1),
                     'growth_pct': round((v24k/v14-1)*100,1)})
idx = pd.DataFrame(idx_rows)
idx.to_csv(f"{OUT}/sexual_violence_index.csv", index=False)

# ---- 4) PER-100k RATES 2024 (for maps) ------------------------------------
# Homicide is the primary (comparable) map; theft/burglary/robbery for the
# interactive dropdown (they show recording-driven geography).
rate_offences = ['homicide','theft','burglary','robbery']
rate = df[(df['unit']=='P_HTHAB')&(df['year']==2024)&
          (df['iccs'].isin([ICCS[k] for k in rate_offences]))&
          (df['value'].notna())].copy()
inv = {ICCS[k]:k for k in rate_offences}
rate['offence'] = rate['iccs'].map(inv)
wide = rate.pivot_table(index='geo', columns='offence', values='value', aggfunc='first')
wide = wide.reset_index()
wide['country'] = wide['geo'].map(lambda g: GEO.get(g,(g,g))[0])
wide['iso3']    = wide['geo'].map(lambda g: GEO.get(g,(g,g))[1])
# keep only geos we can name (drops UK sub-national codes cleanly)
wide = wide[wide['geo'].isin(GEO.keys())]
cols = ['geo','iso3','country'] + [c for c in rate_offences if c in wide.columns]
wide = wide[cols].sort_values('homicide', ascending=False)
wide.to_csv(f"{OUT}/rates_2024.csv", index=False)

# homicide-only convenience file for the static tile-grid map
hom_map = wide[['geo','iso3','country','homicide']].dropna(subset=['homicide']) \
              .sort_values('homicide', ascending=False)
hom_map.to_csv(f"{OUT}/homicide_rate_2024.csv", index=False)

# ---- 5) CORRUPTION context ------------------------------------------------
co = series(ICCS['corruption'])
co_df = pd.DataFrame([{'year':y,'corruption':int(round(v)),'countries':n}
                      for y,(v,n,_) in sorted(co.items())])
co_df.to_csv(f"{OUT}/corruption_trend.csv", index=False)
corr24 = int(co_df.loc[co_df.year==2024,'corruption'].iloc[0])
corr23 = int(co_df.loc[co_df.year==2023,'corruption'].iloc[0])
brib24 = int(round(eu_sum(ICCS['bribery'],2024)[0]))

# ---- 6) master clean long table -------------------------------------------
master = df[df['geo'].isin(EU27)].copy()
master['category'] = master['iccs'].map({v:k for k,v in ICCS.items()})
master.to_csv(f"{OUT}/crime_clean_eu27_long.csv", index=False)

# ===========================================================================
# Print a compact figure sheet (used to hard-code verified numbers elsewhere)
print("=== VERIFIED FIGURE SHEET (EU-27, real crim_off_cat) ===")
print(f"theft_2024            = {theft24:,}")
print(f"homicide_2024         = {hom24:,}")
print(f"theft_to_homicide     = {ratio:.1f}x  (round {round(ratio,-1):.0f})")
print(f"burglary_2024         = {int(comp.loc[comp.key=='burglary','value_2024'].iloc[0]):,}"
      f"  ({int(comp.loc[comp.key=='burglary','countries'].iloc[0])}/27; "
      f"missing {comp.loc[comp.key=='burglary','missing'].iloc[0]})")
print(f"robbery_2024          = {int(comp.loc[comp.key=='robbery','value_2024'].iloc[0]):,}"
      f"  ({int(comp.loc[comp.key=='robbery','countries'].iloc[0])}/27; "
      f"missing {comp.loc[comp.key=='robbery','missing'].iloc[0]})")
print(f"sexual_violence_2024  = {int(comp.loc[comp.key=='sexual_violence','value_2024'].iloc[0]):,} (27/27)")
print("--- theft pandemic round-trip ---")
print(f"theft 2019={v19:,}  2021={v21:,}  2024={v24:,}")
print(f"dip 2021 vs 2019      = {dip:+.1f}%")
print(f"rebound 2024 vs 2021  = {reb:+.1f}%")
print(f"yoy 2024 vs 2023      = {yoy:+.1f}%")
print("--- reporting surge (same basket both endpoints) ---")
for _,r in idx.iterrows():
    print(f"{r['category']:16s} 2014={r['v2014']:,} -> 2024={r['v2024']:,} "
          f"| +{r['growth_pct']:.0f}% | idx {r['index_2024']:.0f} "
          f"| {r['n2024']}/27 | same_basket={r['same_basket']} "
          f"| missing={r['missing'] or '-'}")
print("--- corruption ---")
print(f"corruption 2024={corr24:,} (+{(corr24/corr23-1)*100:.1f}% vs 2023); bribery 2024={brib24:,}")
print("--- map coverage ---")
print(f"countries with homicide rate 2024 = {hom_map.shape[0]}")
print(f"homicide rate range: {hom_map['homicide'].max():.2f} ({hom_map.iloc[0]['country']}) "
      f"-> {hom_map['homicide'].min():.2f} ({hom_map.iloc[-1]['country']})")
tr = wide[['country','theft']].dropna().sort_values('theft',ascending=False)
print(f"theft rate range:    {tr['theft'].max():.0f} ({tr.iloc[0]['country']}) "
      f"-> {tr['theft'].min():.0f} ({tr.iloc[-1]['country']}) "
      f"= {tr['theft'].max()/tr['theft'].min():.0f}x span")
print("\nWrote:", ", ".join(sorted(os.listdir(OUT))))
