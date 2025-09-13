# src/feature_engineering.py
import pandas as pd
import numpy as np
from datetime import datetime
import os, json

from .config import BROAD_CATEGORIES, BROAD_CATEGORY_KEYWORDS, DEFAULT_CURRENCY

# === Загружаем пользовательский словарь категорий ===
_map_path = os.path.join(os.path.dirname(__file__), '../results/category_map.json')
if os.path.exists(_map_path):
    with open(_map_path, 'r', encoding='utf-8') as f:
        _CATEGORY_MAP = json.load(f)
else:
    _CATEGORY_MAP = {}

def map_category_text(s):
    """Сначала ищем категорию в JSON-словаре, затем по ключевым словам."""
    s0 = str(s).strip().lower()
    if s0 in _CATEGORY_MAP:
        return _CATEGORY_MAP[s0]
    for cat, keywords in BROAD_CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in s0:
                return cat
    return 'other'

def aggregate_client_features(cid, trans_df=None, transf_df=None):
    out = {'client_code': cid}
    # transactions
    if trans_df is None or len(trans_df) == 0:
        out.update({f'pct_{c}': 0.0 for c in BROAD_CATEGORIES})
        out.update({'total_spend': 0.0, 'avg_txn': 0.0, 'txn_count': 0,
                    'median_txn': 0.0, 'top3_share': 0.0, 'salary_present': 0})
    else:
        trans = trans_df.copy()
        trans['date'] = pd.to_datetime(trans.get('date', None), errors='coerce')
        trans['amount'] = pd.to_numeric(trans.get('amount', 0), errors='coerce').fillna(0)
        trans['category'] = trans.get('category', '').fillna('').astype(str)
        trans['broad_cat'] = trans['category'].apply(map_category_text)
        total_spend = trans['amount'].sum()
        spend_by_cat = trans.groupby('broad_cat')['amount'].sum().reindex(BROAD_CATEGORIES).fillna(0)
        pct_by_cat = (spend_by_cat / total_spend).fillna(0).to_dict()
        out.update({f'pct_{k}': float(pct_by_cat.get(k, 0.0)) for k in BROAD_CATEGORIES})
        out['total_spend'] = float(total_spend)
        out['avg_txn'] = float(trans['amount'].mean()) if len(trans) > 0 else 0.0
        out['txn_count'] = int(len(trans))
        out['median_txn'] = float(trans['amount'].median()) if len(trans) > 0 else 0.0
        top3 = spend_by_cat.sort_values(ascending=False).head(3).sum()
        out['top3_share'] = float((top3 / total_spend) if total_spend > 0 else 0.0)
        out['salary_present'] = int(trans.get('status', '').astype(str).str.contains('зп', case=False, na=False).any()) if 'status' in trans.columns else 0
        # recency
        if trans['date'].notnull().any():
            last = trans['date'].max()
            out['days_since_last_tx'] = (pd.Timestamp.now() - last).days
        else:
            out['days_since_last_tx'] = None
    # transfers
    if transf_df is None or len(transf_df) == 0:
        out.update({'sum_in': 0.0, 'sum_out': 0.0, 'transfers_count': 0})
    else:
        tr = transf_df.copy()
        tr['amount'] = pd.to_numeric(tr.get('amount', 0), errors='coerce').fillna(0)
        dir_col = tr.get('direction', '').astype(str).str.lower()
        sum_in = tr[dir_col == 'in']['amount'].sum() if 'direction' in tr.columns else 0.0
        sum_out = tr[dir_col == 'out']['amount'].sum() if 'direction' in tr.columns else 0.0
        out['sum_in'] = float(sum_in)
        out['sum_out'] = float(sum_out)
        out['transfers_count'] = int(len(tr))
    # preserve first name if available
    if trans_df is not None and 'name' in trans_df.columns and len(trans_df) > 0:
        full = str(trans_df.iloc[0].get('name', ''))
        out['name'] = full.split()[0] if full else ''
    else:
        out['name'] = ''
    # currency check (fraction of non-default currency)
    non_default = 0
    total_rows = 0
    if trans_df is not None and 'currency' in trans_df.columns:
        total_rows += len(trans_df)
        non_default += (trans_df['currency'].astype(str).str.upper() != DEFAULT_CURRENCY).sum()
    if transf_df is not None and 'currency' in transf_df.columns:
        total_rows += len(transf_df)
        non_default += (transf_df['currency'].astype(str).str.upper() != DEFAULT_CURRENCY).sum()
    out['fraction_non_kzt_tx'] = float(non_default / total_rows) if total_rows > 0 else 0.0
    return out

def build_features_table(clients_dict):
    rows = []
    for cid, parts in clients_dict.items():
        t = parts.get('transactions', pd.DataFrame())
        tr = parts.get('transfers', pd.DataFrame())
        rows.append(aggregate_client_features(cid, t, tr))
    feat = pd.DataFrame(rows).set_index('client_code').fillna(0)
    return feat.reset_index()
