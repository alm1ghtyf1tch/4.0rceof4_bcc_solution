# src/pipeline.py
import os
from .data_loader import load_zip_by_client, load_csv_list
from .feature_engineering import build_features_table
from .ranking import rank_by_benefit
from .push_generator import generate_push
from .config import RESULTS_DIR, PRODUCT_PARAMS
import pandas as pd

def ensure_results_dir():
    path = os.path.join(os.path.dirname(__file__), RESULTS_DIR)
    os.makedirs(path, exist_ok=True)
    return path

def run_pipeline_from_zip(zip_path, save_results=True):
    clients = load_zip_by_client(zip_path)
    features = build_features_table(clients)
    recs = rank_by_benefit(features, top_n=4)
    # merge name into recs for push generation
    features_small = features[['client_code','name']].copy() if 'name' in features.columns else features[['client_code']].copy()
    merged = recs.merge(features_small, on='client_code', how='left')
    # generate push for top1
    pushes = []
    for _, r in merged.iterrows():
        cid = r['client_code']
        name = r.get('name','') if 'name' in r else ''
        top1 = r.get('top1', None)
        top1_benefit = r.get('top1_benefit', 0.0)
        push = generate_push(name, top1, top1_benefit)
        pushes.append(push)
    merged['push_top1'] = pushes
    # expand top_products to columns
    def top_products_to_cols(tp_list):
        out = {}
        for i in range(4):
            if len(tp_list) > i:
                out[f'top{i+1}_product'] = tp_list[i][0]
                out[f'top{i+1}_benefit'] = tp_list[i][1]
            else:
                out[f'top{i+1}_product'] = None
                out[f'top{i+1}_benefit'] = 0.0
        return out
    extra = merged['top_products'].apply(top_products_to_cols).apply(pd.Series)
    final = pd.concat([merged.drop(columns=['top_products']), extra], axis=1)
    if save_results:
        outdir = ensure_results_dir()
        features.to_csv(os.path.join(outdir, 'features.csv'), index=False)
        final.to_csv(os.path.join(outdir, 'recommendations.csv'), index=False)
    return features, final
