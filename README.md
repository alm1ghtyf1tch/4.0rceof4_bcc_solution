# Decentrathon 4.0 — BCC AI Hub — Case 1  
**Решение команды:** Meirbek Zhangir (капитан), Inkarbay Abilmansur, Bari Ilyas, Saltanat Zhangulova

---

## Коротко о проекте
Это репо — финальное решение задачи **Decentrathon 4.0 — Case 1**.  
Наша цель: на основе транзакционных данных и сведений о клиентах автоматизированно рекомендовать банковские продукты (Top-4) и генерировать краткие персонализированные push-уведомления.  

Кроме основного решения по кейсу, в репозитории есть небольшой **бонус — голосовой ассистент** (demo), который можно использовать внутри банка: он помогает сотрудникам/клиентам получать информацию о финансах и продуктах голосом. Бонус описан отдельно в конце README.

---

## Ключевые особенности решения
- Полный end-to-end pipeline: загрузка CSV → построение признаков → расчёт выгоды по продуктам → ранжирование Top-4 → генерация push (шаблон + LLM-рефайн) → сохранение diagnostics + визуализации.
- Архетипы (кластеризация клиентов) для интерпретируемой персонализации.
- Детальная диагностика и breakdown выгод по каждому клиенту (CSV + per-client JSON) — всё для жюри.
- Локальная интеграция LLM (LM Studio) для рефинмента push-сообщений + безопасный fallback к шаблону.
- Простая воспроизводимость: `python3 main.py` (после установки зависимостей и запуска LM Studio).

---

## Команда
- **Капитан** — Meirbek Zhangir  
- **Второй участник** — Inkarbay Abilmansur  
- **Третий участник** — Bari Ilyas  
- **Четвертый участник** — Saltanat Zhangulova

---

## Структура проекта (и краткое описание файлов)
> Ниже — файлы/папки, которые присутствуют в репозитории (или которые мы использовали в разработке). Возле каждого файла — короткое назначение.

project/
├── main.py
├── generate_arch_report.py
├── test.py
├── test_llm.py
├── requirements.txt
├── README.md
├── data/
│ └── case 1/ # входные CSV: client_x_transactions_3m.csv, client_x_transfers_3m.csv, clients.csv
├── results/ # выходные файлы (автоматически создаются)
│ ├── features.csv
│ ├── recommendations.csv
│ ├── recommendations_full_benefits.csv
│ ├── diagnostics_summary.csv
│ ├── diagnostics_per_client/ # per-client JSONs
│ ├── archetypes_profile.csv
│ ├── archetypes_umap.csv
│ ├── archetypes_assignments.csv
│ └── category_map.json # (опционально) ручной словарь маппинга категорий
└── src/
├── data_loader.py # загружает все CSV и формирует dict клиентов: {client_code: {'transactions': df, 'transfers': df}}
├── pipeline.py # (утилита) run_pipeline_from_zip и вспомогательные функции
├── feature_engineering.py # агрегация транзакций -> признаки (pct_*, total_spend, avg_txn, days_since_last_tx, sum_in/out, avg_monthly_balance_kzt и т.д.)
├── config.py # мэппинг ключевых слов в broad categories и PRODUCT_PARAMS (все бизнес-параметры)
├── benefit_calculator.py # правила расчёта выгоды (cashback, депозитные доходы, FX benefit и пр.)
├── ranking.py # ранжирование продуктов по рассчитанной выгоде -> Top-4
├── push_generator.py # шаблонный генератор push (fmt_money, шаблоны по продуктам, simple checks)
├── llm_refiner.py # LLM-рефайнер (LM Studio) — продвинутый, с debug и фолбэком
├── local_refine.py # (опционально) более простой LLM-рефайнер (альтернатива)
├── diagnostics.py # сохранение recommendations_full_benefits, diagnostics_summary, per-client JSON
├── visuals.py # save_cluster_plots, save_client_card (UMAP/KMeans визуализации и индивидуальные карточки)
└── archetypes_utils.py # (опционально) вспомогательные функции: UMAP + KMeans + извлечение профилей архетипов

## Как запустить (локально)
1. **Клонируй репо**

git clone https://github.com/<your-org>/<repo>.git
cd <repo>

3. Создай виртуальное окружение и установи зависимости

4. LM Studio (локальный LLM)
Наш LLM-интегратор использует LM Studio (или другой локальный сервер, совместимый с OpenAI-like HTTP API).

Запусти LM Studio и загрузите модель (например openchat-3.5-1210).

Включи Server → старт сервера. По умолчанию сервер слушает http://localhost:1234 и поддерживает /v1/chat/completions и /v1/completions.

Если ты включил авторизацию — настрой заголовок Authorization в src/llm_refiner.py.

4. Положи входные CSV
В data/case 1/ должны лежать все client_*_transactions_3m.csv, client_*_transfers_3m.csv и (опционально) clients.csv с колонками:
client_code,name,status,age,city,avg_monthly_balance_KZT

5. Запусти основную пайплайн-процедуру
python3 main.py

6. Ключевые точки выполнения

main.py создаёт results/ и сохраняет: features.csv, recommendations.csv, recommendations_full_benefits.csv, diagnostics_summary.csv, diagnostics_per_client/ и т. п.

generate_arch_report.py (если запускать отдельно) генерирует архетипы: archetypes_profile.csv, archetypes_umap.csv, archetypes_assignments.csv.

test_llm.py — быстрый тест LLM-рефайнера (локальный).

Что именно делает pipeline — по шагам (технически и математически)
1) Data ingestion

data_loader.py парсит все .csv. Для каждого client_code собираются transactions и transfers.

Если есть clients.csv — его поля (status, age, city, avg_monthly_balance_KZT) мерджатся в итоговую features таблицу.

2) Feature engineering (feature_engineering.py)

Нормализация колонок date, amount, очистка category текста.

Категоризация: текстовые category → broad_cat (используется BROAD_CATEGORY_KEYWORDS в config.py). Также поддерживается ручной category_map.json в results/ для исправления «странных» категорий.

Признаки:

pct_<category> — доля расходов по широким категориям (food, transport, travel, online, restaurants, entertainment, utilities, health, other).

total_spend, avg_txn, median_txn, txn_count, top3_share (доля top-3 категорий).

salary_present — обнаружение «зп» в колонке status транзакций.

days_since_last_tx — RECENCY.

sum_in, sum_out, transfers_count — из transfers.

fraction_non_kzt_tx — доля транзакций в не-KZT (показатель FX-активности).

avg_monthly_balance_kzt — из clients.csv (важно для тарифных/депозитных решений).

3) Benefit calculation (business logic) — benefit_calculator.py

Для каждого клиента и каждого продукта считаем ожидаемую месячную выгоду (приблизительно в KZT). Основные формулы:

Карта для путешествий
benefit_travel = travel_spend * cashback_travel + transport_spend * cashback_transport
(cashback обычно 4% на travel, 4% на transport — параметры в PRODUCT_PARAMS)

Премиальная карта
tier_cashback = base_cashback если avg_balance < 1_000_000, 0.03 если 1_000_000 <= avg_balance < 6_000_000, 0.04 если avg_balance >= 6_000_000
benefit_premium = total_spend * tier_cashback + sum(bonus_cat_spend * bonus_cb)

учёт экономии по комиссиям (например fee_saving_per_transfer * transfers_count)
(есть ежемесячный cap, например 100 000 ₸)

Кредитная карта
Бонус для 3 любимых категорий (top3):
top3_spend = sum(shares_top3) * total_spend
benefit_credit = top3_spend * favorite_cb + online_spend * online_cb

Депозиты / Инвестиции / Золото
benefit_deposit_monthly ≈ avg_monthly_balance_kzt * (annual_rate / 12)

Обмен валют
fx_volume = fraction_non_kzt_tx * total_spend
benefit_fx = fx_volume * spread_benefit (оценка экономии на обмене)

Кредит наличными
Мы не считаем выгоду в положительном смысле (это продукт с издержками), но можем оценить пригодность.

Все параметры (cashback, caps, annual_rate и т.д.) хранятся в src/config.py в словаре PRODUCT_PARAMS. Это позволяет прозрачной настройки бизнес-логики без изменения кода.

4) Ranking (ranking.py)

Для каждого клиента вызывается estimate_all_products(features_df) — возвращает словарь product -> estimated_benefit.

Сортируем продукты по убыванию выгоды и формируем Top-N (в нашем случае Top-4).

Сохраняем recommendations.csv (Top-4, top1_benefit и др.) и recommendations_full_benefits.csv (полный breakdown).

5) Диагностика (для жюри)

diagnostics_summary.csv — объединение features + топ-продуктов, ключевых метрик.

diagnostics_per_client/<client>_benefits.json — подробный breakdown для каждого клиента (используется на презентации для доказательства корректности рекомендаций).

Эти файлы позволяют показать, почему каждому клиенту был рекомендован тот или иной продукт (прозрачная математика, не «чёрный ящик»).

6) Архетипы (clustering, generate_arch_report.py)

Для удобства и объяснения рекомендаций мы строим архетипы клиентов:

Входные признаки для кластеризации: pct_* (категории расходов), avg_txn, total_spend, txn_count, top3_share, avg_monthly_balance_kzt, fraction_non_kzt_tx и т.д.

Сначала снижаем размерность (UMAP) для визуализации и стабильности.

Затем применяем KMeans (4–6 кластеров — параметр настраиваемый) для выделения архетипов.

Для каждого кластера формируем профиль: средние доли по категориям, средний чек, средний баланс → сохраняем в archetypes_profile.csv.

archetypes_assignments.csv хранит, к какому архетипу отнесён каждый клиент.

Результат: каждый клиент имеет arch_type (архетип) — это используется и в push-контексте (LLM получает архетип в prompt и генерирует более уместный текст).

Push-уведомления (алгоритм)

Шаблонный генератор (push_generator.py) — быстро формирует короткие сообщения по правилам (персонализация имени, формат суммы, CTA), пригодные как fallback.

LLM-рефайнер (llm_refiner.py) — основной механизм генерации высококачественных push:

Собирает контекст: name, product, benefit_str, status, archetype, cats (топ-2 категорий).

Формирует строгий prompt с system message и user message (жёсткие правила: «не использовать приветствий», «1 мысль + 1 CTA», «макс 1 эмодзи», длина ≤200 символов).

Делает POST на локальный LM Studio: /v1/chat/completions (проверяет и /v1/completions как fallback).

Парсит ответ и возвращает текст.

Если LLM не доступен или ответ некорректный — используется fallback шаблон из push_generator.py.

Безопасность/валидность:

В push_generator.py есть simple_post_check() — базовые проверки длины/формата/эмодзи/верхнего регистра.

В llm_refiner.py — ведётся debug логирование (полезно при демонстрации и отладке).

Как настроить локальный LLM (LM Studio)

Установи и открой LM Studio (инструмент для локального запуска моделей).

Загрузите модель (например openchat-3.5-1210) — можно скачать из LM Studio marketplace или Hugging Face (если у тебя скачан локально).

В LM Studio → вкладка Server → Start Server. Обычные URL: http://localhost:1234.

В настройках сервера посмотри доступные endpoint’ы:

POST /v1/chat/completions

POST /v1/completions

POST /v1/embeddings (если нужно)

Если LM Studio включил авторизацию — установи Authorization заголовок в src/llm_refiner.py. По умолчанию авторизация не требуется.

Тест:
python3 test_llm.py
# или
curl -X POST "http://localhost:1234/v1/chat/completions" -d '{"model":"openchat-3.5-1210","messages":[{"role":"user","content":"тест"}]}' -H "Content-Type: application/json"
