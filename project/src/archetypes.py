# src/archetypes.py
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
try:
    import umap
    _HAS_UMAP = True
except Exception:
    _HAS_UMAP = False

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '../results')

def build_cluster_features(features_df):
    """
    Возвращает фрейм, готовый для кластеризации: отбираем pct_*, total_spend, avg_monthly_balance_kzt,
    fraction_non_kzt_tx, txn_count, top3_share, days_since_last_tx.
    """
    cols = []
    cols += [c for c in features_df.columns if c.startswith('pct_')]
    for c in ['total_spend','avg_monthly_balance_kzt','fraction_non_kzt_tx','txn_count','top3_share','days_since_last_tx']:
        if c in features_df.columns:
            cols.append(c)
    feat = features_df[cols].fillna(0).copy()
    # transform days_since_last_tx (cap / fill)
    if 'days_since_last_tx' in feat.columns:
        feat['days_since_last_tx'] = feat['days_since_last_tx'].replace([np.inf, -np.inf], np.nan).fillna(9999)
    return feat, cols

def find_best_k(X, ks=range(2,7)):
    """
    Возвращает метрики silhouette и db для каждого k.
    """
    results = []
    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        sil = silhouette_score(X, labels) if len(set(labels))>1 else -1
        db = davies_bouldin_score(X, labels) if len(set(labels))>1 else np.inf
        results.append({'k':k,'silhouette':sil,'davies_bouldin':db})
    return pd.DataFrame(results)

def run_clustering(features_df, k=4):
    X_raw, used_cols = build_cluster_features(features_df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)
    km = KMeans(n_clusters=k, random_state=42, n_init=20)
    labels = km.fit_predict(X)
    features_df['archetype_id'] = labels
    # profile each cluster
    profile = features_df.groupby('archetype_id').agg({**{c:'mean' for c in used_cols}, 'client_code':'count', 'total_spend':'median'}).rename(columns={'client_code':'count','total_spend':'median_total_spend'})
    # create labels by heuristics (to be refined manually)
    profile = profile.reset_index()
    # heuristics-based labeling - basic
    labels_map = {}
    for _, row in profile.iterrows():
        aid = int(row['archetype_id'])
        # example logic:
        if row.get('pct_travel',0) > 0.25:
            lab = 'Traveler'
        elif row.get('pct_online',0) > 0.35:
            lab = 'Online shopper'
        elif row.get('pct_restaurants',0) > 0.3:
            lab = 'Dining & Lifestyle'
        elif row.get('avg_monthly_balance_kzt',0) > 100000:
            lab = 'Saver / Investor'
        else:
            lab = 'General Spender'
        labels_map[aid] = lab
    features_df['archetype_label'] = features_df['archetype_id'].map(labels_map)
    # save assignments & profile
    os.makedirs(RESULTS_DIR, exist_ok=True)
    features_df[['client_code','archetype_id','archetype_label']].to_csv(os.path.join(RESULTS_DIR,'archtypes_assignments.csv'), index=False)
    profile.to_csv(os.path.join(RESULTS_DIR,'archetypes_profile.csv'), index=False)
    # optional UMAP
    umap_embedding = None
    if _HAS_UMAP:
        reducer = umap.UMAP(random_state=42)
        um = reducer.fit_transform(X)
        umap_embedding = um
        df_um = pd.DataFrame(um, columns=['u1','u2'])
        df_um['client_code'] = features_df['client_code'].values
        df_um['archetype_label'] = features_df['archetype_label'].values
        df_um.to_csv(os.path.join(RESULTS_DIR,'archetypes_umap.csv'), index=False)
    return features_df, profile, umap_embedding
