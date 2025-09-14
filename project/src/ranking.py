# src/ranking.py
import pandas as pd
from .benefit_calculator import estimate_all_products

def rank_by_benefit(features_df, top_n=4):
    """
    Для каждого клиента:
     - вычисляет benefit по всем продуктам (через estimate_all_products)
     - формирует топ-N (product, benefit)
     - возвращает DataFrame с колонками:
         client_code, top_products (list), top1..topN, top1_benefit..topN_benefit
    Также возвращает dict est (client_code -> {product: benefit})
    """
    # est: client_code -> {product: benefit}
    est = estimate_all_products(features_df)

    recs = []
    for _, row in features_df.iterrows():
        cid = row['client_code']
        products = est.get(cid, {})
        # sort by benefit desc
        sorted_p = sorted(products.items(), key=lambda x: -x[1])
        top = sorted_p[:top_n]

        # prepare columns top1..topN and benefits
        out = {'client_code': cid, 'top_products': top}
        for i in range(top_n):
            prod = top[i][0] if i < len(top) else None
            ben  = float(top[i][1]) if i < len(top) else 0.0
            out[f'top{i+1}'] = prod
            out[f'top{i+1}_benefit'] = ben
        recs.append(out)

    recs_df = pd.DataFrame(recs)
    return recs_df, est
