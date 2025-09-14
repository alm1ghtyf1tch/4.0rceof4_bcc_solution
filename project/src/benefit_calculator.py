# src/benefit_calculator.py
from .config import PRODUCT_PARAMS
import math

def estimate_benefit_row(row: dict, product_name: str):
    """
    Оценка месячной выгоды (в KZT) для продукта product_name на основе признаков row.
    row: dict со столбцами из features (total_spend, pct_<cat>, sum_in, sum_out,
         fraction_non_kzt_tx, avg_monthly_balance_kzt (если есть), transfers_count и т.д.)
    """
    total = float(row.get('total_spend', 0.0))
    params = PRODUCT_PARAMS.get(product_name, {})

    def pct(cat):
        # безопасность: возвращаем 0.0 если такого pct_... нет
        return float(row.get(f'pct_{cat}', 0.0))

    # avg balance (если есть), иначе proxy = net inflow
    avg_balance = row.get('avg_monthly_balance_kzt', None)
    if avg_balance is None:
        avg_balance = max(0.0, row.get('sum_in', 0.0) - row.get('sum_out', 0.0))

    # --- Карта для путешествий ---
    if product_name == "Карта для путешествий":
        travel_spend = pct('travel') * total
        transport_spend = pct('transport') * total
        cb_travel = params.get('cashback', {}).get('travel', 0.04)
        cb_transport = params.get('cashback', {}).get('transport', 0.04)
        benefit = travel_spend * cb_travel + transport_spend * cb_transport
        cap = params.get('cap_monthly', None)
        if cap:
            benefit = min(benefit, cap)

    # --- Премиальная карта ---
    elif product_name == "Премиальная карта":
        base = params.get('base_cashback', 0.02)
        tier = base
        try:
            if avg_balance >= 6_000_000:
                tier = 0.04
            elif avg_balance >= 1_000_000:
                tier = 0.03
        except Exception:
            # если avg_balance не числовой — оставляем базовый
            tier = base
        benefit = total * tier
        # бонусные категории (ювелирка/косметика/рестораны и т.д.)
        bonus = 0.0
        for cat, cb in params.get('bonus_categories_cashback', {}).items():
            bonus += pct(cat) * total * cb
        benefit += bonus
        # экономия на платах за переводы (если задано)
        fee_saving = float(row.get('transfers_count', 0)) * params.get('fee_saving_per_transfer', 0.0)
        benefit += fee_saving
        cap = params.get('cashback_monthly_cap', None)
        if cap:
            benefit = min(benefit, cap)

    # --- Кредитная карта ---
        # --- Кредитная карта (исправленный, с eligibility_factor и cap) ---
    elif product_name == "Кредитная карта":
        # собираем топ-3 категорий
        pct_cols = [k for k in row.keys() if str(k).startswith('pct_')]
        cat_shares = [(c.replace('pct_', ''), row.get(c, 0.0)) for c in pct_cols]
        top3 = sorted(cat_shares, key=lambda x: -x[1])[:3]
        top3_spend = sum([share * total for _, share in top3])

        # параметры из конфига (fallback значения)
        fav_cb = params.get('favorite_cb', 0.10)
        online_cb = params.get('online_cb', fav_cb)
        eligibility = params.get('eligibility_factor', 0.15)
        cap = params.get('cashback_monthly_cap', None)

        # считаем реально-eligible объёмы (консервативная оценка)
        eligible_top3 = top3_spend * eligibility
        bonus1 = eligible_top3 * fav_cb

        # online services отдельно (применяем тот же eligibility)
        online_share = pct('online') + pct('entertainment')
        online_spend = online_share * total
        eligible_online = online_spend * eligibility
        bonus2 = eligible_online * online_cb

        benefit = bonus1 + bonus2
        if cap:
            benefit = min(benefit, cap)

    # --- Обмен валют ---
    elif product_name == "Обмен валют":
        fx_vol = row.get('fraction_non_kzt_tx', 0.0) * total
        spread = params.get('spread_benefit', 0.002)
        benefit = fx_vol * spread

    # --- Кредит наличными (не считаем положительную выгоду) ---
    elif product_name == "Кредит наличными":
        benefit = 0.0

    # --- Депозиты / Инвестиции / Золото: месячная доходность от avg_balance ---
    elif product_name.startswith("Депозит") or product_name in ("Инвестиции", "Золотые слитки"):
        annual = params.get('annual_rate', 0.0)
        benefit = float(avg_balance) * (annual / 12.0)

    else:
        benefit = 0.0

    # Защита от NaN/нечисла
    if not isinstance(benefit, (int, float)) or benefit != benefit:
        benefit = 0.0
    return float(benefit)


def estimate_all_products(features_df):
    """
    Для каждого клиента считает выгоду по всем продуктам, возвращает dict client_code -> {product: benefit, ...}
    """
    products = list(PRODUCT_PARAMS.keys())
    res = {}
    for _, row in features_df.iterrows():
        cid = row['client_code']
        rowd = row.to_dict()
        est = {p: estimate_benefit_row(rowd, p) for p in products}
        res[cid] = est
    return res
