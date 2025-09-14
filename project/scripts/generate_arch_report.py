#!/usr/bin/env python3
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd, os
from src.archetypes import run_clustering, find_best_k, build_cluster_features
import matplotlib.pyplot as plt

RESULTS = os.path.join(os.path.dirname(__file__),'../results')
os.makedirs(RESULTS, exist_ok=True)

# load features
f = pd.read_csv('/Users/laflame8512/Desktop/decentrathon4.0/results/features.csv')  # убедись, что эта версия актуальна

# try to find best k
X_raw, _ = build_cluster_features(f)
from sklearn.preprocessing import StandardScaler
X = StandardScaler().fit_transform(X_raw)
from src.archetypes import find_best_k
ks = find_best_k(X, ks=range(2,7))
ks.to_csv(os.path.join(RESULTS,'cluster_k_candidates.csv'), index=False)
print("k candidates metrics:\n", ks)

# choose k (you can tweak) — default 4
k = 4
f2, profile, umap_embed = run_clustering(f, k=k)

# save merged recommendations + archetype (if recommendations exist)
if os.path.exists(os.path.join(RESULTS,'recommendations.csv')):
    recs = pd.read_csv(os.path.join(RESULTS,'recommendations.csv'))
    merged = recs.merge(f2[['client_code','archetype_label']], on='client_code', how='left')
    merged.to_csv(os.path.join(RESULTS,'recommendations_with_archetypes.csv'), index=False)

# basic plots
# top1 distribution by archetype
if os.path.exists(os.path.join(RESULTS,'recommendations.csv')):
    recs = pd.read_csv(os.path.join(RESULTS,'recommendations.csv'))
    merged = recs.merge(f2[['client_code','archetype_label']], on='client_code', how='left')
    ct = merged.groupby('archetype_label')['top1'].value_counts().unstack(fill_value=0)
    ct.plot(kind='bar', stacked=True, figsize=(10,6)); plt.title('Top1 per archetype'); plt.tight_layout()
    plt.savefig(os.path.join(RESULTS,'plots','top1_per_archetype.png'))

# mean benefit per product (if full benefits available)
if os.path.exists(os.path.join(RESULTS,'recommendations_full_benefits.csv')):
    est = pd.read_csv(os.path.join(RESULTS,'recommendations_full_benefits.csv')).set_index('client_code')
    est.mean().sort_values(ascending=False).plot(kind='barh', figsize=(8,6))
    plt.title('Mean monthly benefit per product'); plt.tight_layout()
    plt.savefig(os.path.join(RESULTS,'plots','mean_benefit_per_product.png'))

print("Archetypes and plots saved to results/")
