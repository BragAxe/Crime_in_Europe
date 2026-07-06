#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bundle the clean tables into one JSON blob for the interactive dashboard."""
import os, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE)=="scripts" else HERE
DATA = os.path.join(ROOT, "data")

comp = pd.read_csv(f"{DATA}/composition_2024.csv")
tt   = pd.read_csv(f"{DATA}/theft_trend.csv")
idx  = pd.read_csv(f"{DATA}/sexual_violence_index.csv")
rates= pd.read_csv(f"{DATA}/rates_2024.csv")

blob = {
 "composition": {
    "category": comp["category"].tolist(),
    "value":    [int(v) for v in comp["value_2024"]],
 },
 "theft_trend": {
    "year":  [int(y) for y in tt["year"]],
    "value": [int(v) for v in tt["theft"]],
    "index": [float(v) for v in tt["index_2019"]],
 },
 "sv_index": {
    "category": idx["category"].tolist(),
    "v2014":    [int(v) for v in idx["v2014"]],
    "v2024":    [int(v) for v in idx["v2024"]],
    "index":    [float(v) for v in idx["index_2024"]],
    "growth":   [float(v) for v in idx["growth_pct"]],
 },
 "rates": {
    "iso3":     rates["iso3"].tolist(),
    "country":  rates["country"].tolist(),
    "homicide": [None if pd.isna(v) else float(v) for v in rates.get("homicide", [])],
    "theft":    [None if pd.isna(v) else float(v) for v in rates.get("theft", [])],
    "burglary": [None if pd.isna(v) else float(v) for v in rates.get("burglary", [])],
    "robbery":  [None if pd.isna(v) else float(v) for v in rates.get("robbery", [])],
 },
}
with open(f"{DATA}/dashboard_data.json", "w") as f:
    json.dump(blob, f, ensure_ascii=False, separators=(",", ":"))
print("wrote dashboard_data.json  (", len(json.dumps(blob)), "bytes )")
print("rate rows:", len(blob["rates"]["iso3"]))
