import glob, os, pandas as pd
from collections import Counter

# путь к папке, где лежат CSV transactions
csv_dir = 'data/case 1'  # подстрой под свой путь
paths = [p for p in glob.glob(os.path.join(csv_dir, '*.csv')) if 'transactions' in os.path.basename(p)]
cnt = Counter()

for p in paths:
    df = pd.read_csv(p)
    if 'category' in df.columns:
        cats = df['category'].astype(str).str.strip().str.lower()
        cnt.update([c for c in cats if c])

most = cnt.most_common()
pd.DataFrame(most, columns=['category','count']).to_csv('results/category_counts.csv', index=False)
print('Сохранено: results/category_counts.csv — открой, посмотри топ 50 категорий')
