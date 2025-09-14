import os
import matplotlib.pyplot as plt

def save_cluster_plots(features_df, recs_df, outdir='results'):
    """
    Сохраняет:
    - top1_counts.png (частота топ-1 продукта)
    - benefit_hist.png (распределение выгоды)
    """
    os.makedirs(outdir, exist_ok=True)

    # Топ-1 продукты
    top1_counts = recs_df['top1'].value_counts()
    plt.figure(figsize=(6, 4))
    top1_counts.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title('Количество клиентов по рекомендованным картам (Top-1)')
    plt.ylabel('Количество клиентов')
    plt.xlabel('Продукт')
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, 'top1_counts.png'), dpi=150)
    plt.close()

    # Гистограмма выгоды
    plt.figure(figsize=(6, 4))
    recs_df['top1_benefit'].plot(kind='hist', bins=30, color='salmon', edgecolor='black')
    plt.title('Распределение ожидаемой выгоды по Top-1 продукту')
    plt.xlabel('Ожидаемая выгода (в валюте)')
    plt.ylabel('Количество клиентов')
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, 'benefit_hist.png'), dpi=150)
    plt.close()

def save_client_card(features_df, recs_df, client_code, outdir='results'):
    """
    Сохраняет bar-чарт процентов расходов по категориям для конкретного клиента
    """
    os.makedirs(outdir, exist_ok=True)
    row = features_df[features_df['client_code'] == client_code].iloc[0]
    pct_cols = [c for c in features_df.columns if c.startswith('pct_')]
    vals = [row[c] for c in pct_cols]
    cats = [c.replace('pct_', '') for c in pct_cols]

    plt.figure(figsize=(8, 4))
    plt.bar(cats, vals, color='lightgreen', edgecolor='black')
    plt.title(f'Клиент {client_code}: доля расходов по категориям')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Доля (0–1)')
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, f'client_{client_code}_card.png'), dpi=150)
    plt.close()
