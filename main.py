#!/usr/bin/env python3
# main.py
# Полный pipeline: загрузка CSV -> признаки -> ранжирование (Top-4) -> пуши -> сохранение результатов/диагностики/визуалов

import glob
import os
import pandas as pd
import traceback

from src.data_loader import load_csv_list
from src.feature_engineering import build_features_table
from src.push_generator import generate_push
# try import local LLM refine (optional)
try:
    from src.local_refine import refine_push
    _HAS_LOCAL_REFINER = True
except Exception:
    refine_push = None
    _HAS_LOCAL_REFINER = False

# ranking (ожидается, что rank_by_benefit возвращает (recs_df, est_dict))
from src.ranking import rank_by_benefit

# diagnostics utilities (создаёт breakdown выгоды и summary)
from src.diagnostics import save_full_benefits, save_diagnostics_summary, save_per_client_json

# visuals (опционально)
try:
    from src.visuals import save_cluster_plots, save_client_card
    _HAS_VISUALS = True
except Exception:
    _HAS_VISUALS = False


# === Настройки путей ===
CSV_DIR = '/Users/laflame8512/Desktop/decentrathon4.0/project/data/case 1'  # подстрой, если нужно
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '../results')
os.makedirs(RESULTS_DIR, exist_ok=True)


def main():
    print("Start pipeline")

    # 1) Найти CSV
    file_paths = glob.glob(os.path.join(CSV_DIR, '*.csv'))
    if not file_paths:
        raise RuntimeError(f'В папке {CSV_DIR} не найдено csv-файлов')
    print(f"Найдено {len(file_paths)} csv-файлов")

    # 2) Загрузить все CSV в структуру клиентов
    print("Загрузка файлов клиентов...")
    clients = load_csv_list(file_paths)
    print(f"Загружено клиентов: {len(clients)}")

    # 3) Построить таблицу признаков
    print("Построение признаков (features)...")
    features = build_features_table(clients)
    features_path = os.path.join(RESULTS_DIR, 'features.csv')
    features.to_csv(features_path, index=False)
    print(f"Features сохранены: {features_path}")
    print("Признаки (первые строки):")
    print(features.head())

    # 4) Ранжирование (Top-N)
    print("Считаем выгоды и ранжируем продукты (Top-4)...")
    try:
        recs_obj = rank_by_benefit(features, top_n=4)
        # rank_by_benefit может возвращать либо (recs_df, est) либо только recs_df
        if isinstance(recs_obj, tuple) and len(recs_obj) == 2:
            recs_df, est_dict = recs_obj
        else:
            recs_df = recs_obj
            # если estimate_all_products был не возвращён, вычислим заново (fallback)
            try:
                from src.benefit_calculator import estimate_all_products
                est_dict = estimate_all_products(features)
            except Exception:
                est_dict = {}
                print("Warning: не удалось получить полный breakdown выгод (est_dict).")
    except Exception as e:
        print("Error during ranking:", e)
        traceback.print_exc()
        raise

    # 5) Сгенерировать пуши для top1
    print("Генерируем push для top1...")
    pushes = []
    for _, r in recs_df.iterrows():
        cid = r['client_code']
        # получить имя
        if 'name' in features.columns:
            name_values = features.loc[features['client_code'] == cid, 'name'].values
            name = name_values[0] if len(name_values) > 0 else ''
        else:
            name = ''

        product = r.get('top1') if 'top1' in r else None
        benefit = r.get('top1_benefit', 0.0) if 'top1_benefit' in r else 0.0

        # build simple context: top-2 categories names
        pct_cols = [c for c in features.columns if c.startswith('pct_')]
        cats = ""
        try:
            frow = features[features['client_code'] == cid].iloc[0]
            topcats = sorted([(c.replace('pct_', ''), float(frow[c])) for c in pct_cols], key=lambda x: -x[1])[:2]
            cats = ", ".join([cat for cat, _ in topcats if _ > 0])
        except Exception:
            cats = ""

        # first try local refiner (LM Studio / Ollama) if available
        push_text = None
        if _HAS_LOCAL_REFINER and product is not None:
            try:
                # refine_push signature: refine_push(name, product, benefit_str, reasons)
                reasons = cats
                benefit_str = f"≈{int(round(float(benefit)))} ₸" if benefit else ""
                push_text = refine_push(name, product, benefit_str, reasons)
            except Exception as e:
                # fall back
                print(f"Local refiner failed for client {cid}: {e}")
                push_text = None

        # fallback to template generator
        if not push_text:
            try:
                push_text = generate_push(name, product, float(benefit), currency='KZT', context={'cats': cats})
            except Exception as e:
                print("generate_push failed:", e)
                push_text = f"{name or 'Здравствуйте'}, рекомендуем {product}. Подробнее в приложении."

        pushes.append(push_text)

    recs_df['push_top1'] = pushes

    # 6) Сохранить базовый recommendations.csv (Top-N)
    recs_path = os.path.join(RESULTS_DIR, 'recommendations.csv')
    recs_df.to_csv(recs_path, index=False)
    print(f"Recommendations (Top-4) сохранены: {recs_path}")
    print(recs_df.head())

    # 7) Сохранить полный breakdown выгод (для жюри)
    try:
        full_benefits_path = os.path.join(RESULTS_DIR, 'recommendations_full_benefits.csv')
        save_full_benefits(est_dict, out_path=full_benefits_path)
        print(f"Full benefits breakdown сохранён: {full_benefits_path}")
    except Exception as e:
        print("Не удалось сохранить full benefits:", e)

    # 8) Сохранить diagnostics summary (features + топы)
    try:
        diag_path = os.path.join(RESULTS_DIR, 'diagnostics_summary.csv')
        save_diagnostics_summary(features, recs_df, out_path=diag_path)
        print(f"Diagnostics summary сохранён: {diag_path}")
    except Exception as e:
        print("Не удалось сохранить diagnostics summary:", e)

    # 9) Сохранить per-client json (опционально, удобно для презентации)
    try:
        json_dir = os.path.join(RESULTS_DIR, 'diagnostics_per_client')
        save_per_client_json(est_dict, out_dir=json_dir)
        print(f"Per-client JSONs сохранены в: {json_dir}")
    except Exception as e:
        print("Не удалось сохранить per-client JSON:", e)

    # 10) Визуализации (если присутствует модуль visuals)
    if _HAS_VISUALS:
        try:
            print("Сохраняем общие графики кластеров...")
            save_cluster_plots(features, recs_df, out_dir=RESULTS_DIR)
            print("Сохраняем карточки клиентов (10 случайных)...")
            sample_clients = features['client_code'].sample(min(10, len(features))).tolist()
            for cid in sample_clients:
                try:
                    save_client_card(features, recs_df, client_code=cid, out_dir=RESULTS_DIR)
                except Exception as e:
                    print(f"Не удалось сохранить карточку клиента {cid}: {e}")
            print("Графики сохранены в папке results/")
        except Exception as e:
            print("Ошибка при сохранении визуализаций:", e)
    else:
        print("Модуль visuals не обнаружен — пропускаем генерацию графиков.")

    print("Pipeline finished successfully.")


if __name__ == "__main__":
    main()
