import glob
import os
import pandas as pd

from src.data_loader import load_csv_list
from src.feature_engineering import build_features_table
from src.ranking import rank_by_benefit
from src.push_generator import generate_push
from src.local_refine import refine_push


# === Путь к папке с CSV (у тебя лежит в data/case 1) ===
csv_dir = '/Users/laflame8512/Desktop/decentrathon4.0/project/data/case 1'

# собираем список всех CSV
file_paths = glob.glob(os.path.join(csv_dir, '*.csv'))
if not file_paths:
    raise RuntimeError(f'В папке {csv_dir} не найдено csv-файлов')

# загружаем в словарь клиентов
clients = load_csv_list(file_paths)

# строим признаки
features = build_features_table(clients)

# считаем рекомендации
recs = rank_by_benefit(features, top_n=4)

# генерим пуш для top1
pushes = []
for _, r in recs.iterrows():
    cid = r['client_code']
    # имя для пуша
    if 'name' in features.columns:
        name_values = features.loc[features['client_code'] == cid, 'name'].values
        name = name_values[0] if len(name_values) > 0 else ''
    else:
        name = ''
    push = generate_push(name, r['top1'], r['top1_benefit'])
    pushes.append(push)

recs['push_top1'] = pushes

# сохраняем результаты рядом с main.py
features.to_csv('features.csv', index=False)
recs.to_csv('recommendations.csv', index=False)

print('Готово. Первые строки рекомендаций:')
print(recs.head())

from src.visuals import save_cluster_plots, save_client_card

# Общие графики
save_cluster_plots(features, recs)

# Графики всех клиентов
for cid in features['client_code'].sample(10):  # только 10 случайных
    save_client_card(features, recs, client_code=cid)

print("Графики сохранены в папке results/")
