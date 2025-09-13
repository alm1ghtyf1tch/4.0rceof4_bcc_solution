# src/benefit_calculator.py
from .config import PRODUCT_PARAMS
import math

def estimate_benefit_row(row: dict, product_name: str):
    """
    Оценивает месячную выгоду (в той же валюте, что и транзакции) для данного клиента (row - dict из features).
    Возвращает float (приблизительная экономия/доход в месяц).
    """
    total = float(row.get('total_spend', 0.0))
    if product_name == 'Travel Card':
        travel_spend = row.get('pct_travel', 0.0) * total
        transport_spend = row.get('pct_transport', 0.0) * total
        params = PRODUCT_PARAMS.get('Travel Card', {})
        travel_cb = params.get('cashback', {}).get('travel', 0.03)
        taxi_cb = params.get('cashback', {}).get('transport', 0.04)
        benefit = travel_spend * travel_cb + transport_spend * taxi_cb
    elif product_name == 'Shopper Card':
        online_spend = row.get('pct_online', 0.0) * total
        food_spend = row.get('pct_food', 0.0) * total
        params = PRODUCT_PARAMS.get('Shopper Card', {})
        benefit = online_spend * params.get('cashback', {}).get('online', 0.05) + food_spend * params.get('cashback', {}).get('food', 0.03)
    elif product_name == 'Premium Card':
        params = PRODUCT_PARAMS.get('Premium Card', {})
        benefit = total * params.get('general_cashback', 0.02) + total * params.get('premium_bonus', 0.0)
    elif product_name == 'Everyday Card':
        params = PRODUCT_PARAMS.get('Everyday Card', {})
        benefit = total * params.get('general_cashback', 0.01)
    elif product_name == 'Deposit':
        params = PRODUCT_PARAMS.get('Deposit', {})
        # грубая оценка: свободные средства = sum_in - sum_out (если положительны), годовой процент -> месячный доход
        free_balance = max(0.0, row.get('sum_in', 0.0) - row.get('sum_out', 0.0))
        annual = params.get('annual_rate', 0.06)
        benefit = free_balance * (annual / 12.0)
    else:
        benefit = 0.0
    # защита от нанов
    if not isinstance(benefit, (int, float)) or benefit != benefit:
        benefit = 0.0
    return float(benefit)

def estimate_all_products(features_df):
    """
    Для каждого клиента считает выгоду по всем продуктам, возвращает словарь client_code -> {product: benefit, ...}
    """
    products = list(PRODUCT_PARAMS.keys())
    res = {}
    for _, row in features_df.iterrows():
        cid = row['client_code']
        rowd = row.to_dict()
        est = {p: estimate_benefit_row(rowd, p) for p in products}
        res[cid] = est
    return res
