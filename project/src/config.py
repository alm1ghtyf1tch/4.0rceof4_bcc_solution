# src/config.py
# Конфигурация: мэппинг категорий и параметры продуктов (параметры — примерные, замените при необходимости)

BROAD_CATEGORY_KEYWORDS = {
    'travel': ['ави', 'отел', 'такси', 'билет', 'тур', 'booking', 'air', 'hotel', 'travel', 'путеш'],
    'transport': ['такси', 'метро', 'автобус', 'самокат', 'трансфер', 'transport', 'uber', 'bolt'],
    'food': ['супермаркет', 'продукт', 'продукты', 'магазин', 'market', 'grocery'],
    'restaurants': ['ресторан', 'кафе', 'бар', 'рестора', 'еда', 'dine', 'restaurant'],
    'online': ['онлайн', 'wildberries', 'ozon', 'aliexpress', 'shop', 'marketplace', 'internet'],
    'entertainment': ['кино', 'театр', 'игра', 'смотр', 'развлеч', 'entertain', 'game'],
    'utilities': ['коммун', 'жкх', 'интернет', 'оплат', 'телефон', 'utilities'],
    'health': ['аптека', 'медици', 'стомат', 'clinic', 'health']
}
# Категорийная последовательность (используется при агрегации)
BROAD_CATEGORIES = list(BROAD_CATEGORY_KEYWORDS.keys()) + ['other']

PRODUCT_PARAMS = {
    "Карта для путешествий": {
        "cashback": {"travel": 0.04, "transport": 0.04},
        "cap_monthly": None  # при наличии лимита, ставьте число в KZT
    },
    "Премиальная карта": {
        "base_cashback": 0.02,
        # дополнительные ступени будут рассчитаны по avg_monthly_balance_kzt:
        # 1-6 млн -> 0.03, >6 млн -> 0.04
        "bonus_categories_cashback": {"jewelry": 0.04, "cosmetics": 0.04, "restaurants": 0.04},
        "fee_saving_per_transfer": 0.0,
        "cashback_monthly_cap": 100000.0
    },
    "Кредитная карта": {
    "favorite_cb": 0.10,
    "online_cb": 0.10,
    "eligibility_factor": 0.15,       # доля топ3 трат, реально попадающая под 10% (настраиваемо)
    "cashback_monthly_cap": 100000.0  # месячный лимит кешбэка (KZT), настраиваемо
    },
    "Обмен валют": {
        "spread_benefit": 0.002  # 0.2% экономии на объёме FX
    },
    "Кредит наличными": {
        "rate": 0.12  # не считаем выгоду как положительную в обычном смысле
    },
    "Депозит Мультивалютный": {
        "annual_rate": 0.145
    },
    "Депозит Сберегательный": {
        "annual_rate": 0.165
    },
    "Депозит Накопительный": {
        "annual_rate": 0.155
    },
    "Инвестиции": {
        "annual_rate": 0.10  # условный годовой доход (оценка), используем для free_balance
    },
    "Золотые слитки": {
        "annual_rate": 0.05  # условная оценка долгосрочной доходности/хранения
    }
}




# Общие настройки
DEFAULT_CURRENCY = 'KZT'
RESULTS_DIR = '../results'  # относительно src/, создаётся pipeline-ом
