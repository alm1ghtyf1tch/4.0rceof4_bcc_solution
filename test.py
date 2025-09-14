import pandas as pd
f = pd.read_csv('features.csv')
r = pd.read_csv('recommendations.csv')

# 1) Распределение топ1
print(r['top1'].value_counts())

# 2) Как много клиентов имеют положительный avg_balance (или sum_in > sum_out)
print("positive avg_balance:", (f['avg_monthly_balance_kzt']>0).sum())
print("positive net_flow:", ((f['sum_in'] - f['sum_out'])>0).sum())

# 3) Разброс total_spend
print(f['total_spend'].describe())

# 4) Сколько клиентов с fraction_non_kzt_tx > 0.01
print((f['fraction_non_kzt_tx']>0.01).sum())

# 5) Средняя выгода по продуктам (собери est_dict, если есть)
est = pd.read_csv('/Users/laflame8512/Desktop/decentrathon4.0/results/recommendations_full_benefits.csv') # если есть
print(est.describe())

# 6) Для примера: разбивка benefits для 5 клиентов
print(est.set_index('client_code').T.iloc[:,:5])
