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

# Продукты и их примерные параметры (cashback в долях, процент в год для депозита)
PRODUCT_PARAMS = {
    'Travel Card': {
        'cashback': {'travel': 0.03, 'transport': 0.04},
        'cap': None
    },
    'Shopper Card': {
        'cashback': {'online': 0.05, 'food': 0.03},
        'cap': None
    },
    'Premium Card': {
        'cashback': {'restaurants': 0.04, 'entertainment': 0.03},
        'general_cashback': 0.02,
        'cap': None
    },
    'Everyday Card': {
        'cashback': {'food': 0.01, 'utilities': 0.01},
        'general_cashback': 0.01,
        'cap': None
    },
    'Deposit': {
        'annual_rate': 0.06  # годовой
    }
}

# Общие настройки
DEFAULT_CURRENCY = 'KZT'
RESULTS_DIR = '../results'  # относительно src/, создаётся pipeline-ом
