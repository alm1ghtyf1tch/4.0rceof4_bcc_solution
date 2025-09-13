# src/ranking.py
import pandas as pd
from .benefit_calculator import estimate_all_products

def rank_by_benefit(features_df, top_n=4):
    """
    Простой ранжировщик: сортируем продукты по estimated_benefit.
    Возвращаем recommendations DataFrame: client_code, top_products(list of tuples (product, benefit)), top1, top1_benefit
    """
    est = estimate_all_products(features_df)
    recs = []
    for _, row in features_df.iterrows():
        cid = row['client_code']
        products = est.get(cid, {})
        sorted_p = sorted(products.items(), key=lambda x: -x[1])
        top = sorted_p[:top_n]
        recs.append({
            'client_code': cid,
            'top_products': top,
            'top1': top[0][0] if top else None,
            'top1_benefit': top[0][1] if top else 0.0
        })
    recs_df = pd.DataFrame(recs)
    return recs_df
