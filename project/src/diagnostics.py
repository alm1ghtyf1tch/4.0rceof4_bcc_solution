# src/diagnostics.py
import os
import pandas as pd
import json

def save_full_benefits(est_dict, out_path='results/recommendations_full_benefits.csv'):
    """
    est_dict: {client_code: {product: benefit, ...}, ...}
    Сохраняет таблицу с одной строкой на клиента и колонкой для каждого продукта.
    """
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    rows = []
    all_products = set()
    for cid, pdict in est_dict.items():
        all_products.update(pdict.keys())
    all_products = sorted(all_products)

    for cid, pdict in est_dict.items():
        row = {'client_code': cid}
        for p in all_products:
            row[p] = float(pdict.get(p, 0.0))
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    return df

def save_diagnostics_summary(features_df, recs_df, out_path='results/diagnostics_summary.csv'):
    """
    Собирает ключевые признаки и топ-N в один CSV:
    client_code, total_spend, avg_monthly_balance_kzt, net_flow, fraction_non_kzt_tx,
    top3_share, transfers_count, pct_*..., top1..topN, top1_benefit..topN_benefit
    """
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    # ensure net_flow column
    feats = features_df.copy()
    if 'avg_monthly_balance_kzt' not in feats.columns:
        feats['avg_monthly_balance_kzt'] = (feats.get('sum_in', 0.0) - feats.get('sum_out', 0.0)).clip(lower=0.0)

    feats['net_flow'] = feats.get('sum_in', 0.0) - feats.get('sum_out', 0.0)

    # select pct_* columns
    pct_cols = [c for c in feats.columns if c.startswith('pct_')]
    keep_cols = ['client_code','total_spend','avg_monthly_balance_kzt','net_flow',
                 'fraction_non_kzt_tx','top3_share','transfers_count'] + pct_cols
    keep_cols = [c for c in keep_cols if c in feats.columns]

    # merge with recs
    merged = feats[keep_cols].merge(recs_df, on='client_code', how='left')
    merged.to_csv(out_path, index=False)
    return merged

def save_per_client_json(est_dict, out_dir='results/diagnostics_per_client'):
    """
    Сохраняет для каждого клиента JSON-файл с benefit breakdown и пустым пояснением.
    useful for presentation (one file per client).
    """
    os.makedirs(out_dir, exist_ok=True)
    for cid, pdict in est_dict.items():
        data = {
            "client_code": cid,
            "benefits": {p: float(v) for p, v in pdict.items()}
        }
        fn = os.path.join(out_dir, f'client_{cid}_benefits.json')
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return out_dir
