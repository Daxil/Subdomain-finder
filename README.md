# recon-pipeline

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3%2B-brightgreen?style=flat-square&logo=celery)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-red?style=flat-square&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

Асинхронный пайплайн для разведки поддоменов. Закидываешь домен — получаешь список поддоменов. Всё сохраняется в базе, обработка идёт через очередь задач.

Сделано для Bug Bounty и пентест-задач, где нужно быстро и чисто собирать поверхность атаки.

---

## Как это работает

```
  [ run.py ]
      │
      ▼
  PostgreSQL  ←──  создаём Job (pending)
      │
      ▼
   Redis  ──────── кидаем задачу в очередь
      │
      ▼
  Celery Worker
      │
      ├── запускает subfinder
      ├── парсит JSON-вывод
      └── пишет результат обратно в PostgreSQL (completed)
      │
      ▼
  [ вывод в терминал ]
```

Celery-воркер и subfinder работают независимо от основного процесса — можно запускать несколько сканов параллельно.

---

## Стек

| Компонент | Зачем |
|-----------|-------|
| **subfinder** | пассивный поиск поддоменов по открытым источникам |
| **Celery** | очередь задач, асинхронное выполнение |
| **Redis** | брокер сообщений для Celery |
| **PostgreSQL** | хранение целей и результатов сканов |
| **SQLAlchemy** | ORM, чтобы не писать сырой SQL |
| **Docker Compose** | поднимает Postgres + Redis одной командой |

---

## Требования

- Python 3.10+
- Docker + Docker Compose
- [subfinder](https://github.com/projectdiscovery/subfinder) — должен быть в PATH

Установка subfinder (если ещё нет):
```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```
или через пакетный менеджер на Kali:
```bash
apt install subfinder
```

---

## Установка и запуск

### 1. Клонируй репо

```bash
git clone https://github.com/your-username/recon-pipeline.git
cd recon-pipeline
```

### 2. Виртуальное окружение и зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Конфиг

```bash
cp .env.example .env
```

Открой `.env` и подправь под себя — там логин/пароль для Postgres и строка подключения к Redis. По умолчанию всё уже настроено для локального запуска через Docker.

### 4. Поднять инфраструктуру

```bash
docker compose up -d
```

Это запустит PostgreSQL на порту `5433` и Redis на порту `6380`.

### 5. Инициализировать базу данных

```bash
python init_db.py
```

### 6. Запустить Celery-воркер

В отдельном терминале (или в tmux):

```bash
celery -A app.celery_app worker --loglevel=info
```

---

## Использование

### Скан домена

```bash
python run.py example.com
```

Пример вывода:
```
Target: example.com
Task in queue (Redis) and wait worker...

Success! Found subdomain : 47

==================================================
api.example.com
dev.example.com
mail.example.com
stage.example.com
vpn.example.com
...
==================================================
DB cleared
```

### Проверить последние задачи в базе

```bash
python check_db.py
```

```
=== ПОСЛЕДНИЕ ЗАДАЧИ СКАНИРОВАНИЯ ===

🔹 Job ID: 12 | Домен: hackerone.com
   Статус: completed
   🎯 Найдено поддоменов: 83
   Примеры: ['api.hackerone.com', 'docs.hackerone.com', ...]
```

### Очистить базу

```bash
python clear_db.py
```

---

## Структура проекта

```
recon-pipeline/
├── app/
│   ├── celery_app.py       # инициализация Celery
│   ├── config.py           # настройки из .env
│   ├── database.py         # подключение к PostgreSQL
│   ├── models.py           # модели Target и ScanJob
│   ├── tasks/
│   │   └── recon.py        # Celery-таска: запуск subfinder и сохранение результата
│   └── workers/
│       └── subdomain.py
├── run.py                  # точка входа: запустить скан и дождаться результата
├── trigger_scan.py         # быстро кинуть задачу в очередь без ожидания
├── check_db.py             # посмотреть последние задачи
├── init_db.py              # создать таблицы в БД
├── clear_db.py             # очистить базу
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Переменные окружения

```env
POSTGRES_USER=recon_user
POSTGRES_PASSWORD=root
POSTGRES_DB=recon_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

REDIS_URL=redis://localhost:6380/0

# опционально — уведомления в телегу
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

> Порты 5433 и 6380 намеренно сдвинуты, чтобы не конфликтовать с другими инстансами Postgres и Redis на машине.

---

## Статусы задач

| Статус | Описание |
|--------|----------|
| `pending` | задача создана, ждёт воркера |
| `running` | subfinder запущен |
| `completed` | результаты сохранены |
| `failed` | что-то пошло не так (подробности в `results.error`) |

---

## Возможные проблемы

**`subfinder не найден в системе`** — subfinder не в PATH. Проверь: `which subfinder`

**`Connection refused` при подключении к БД** — Docker не поднят или порт занят. Проверь: `docker compose ps`

**Таска висит в `pending`** — воркер не запущен. Запусти `celery -A app.celery_app worker --loglevel=info`

**`psycopg2` ошибки** — убедись что установлен `psycopg2-binary`, не `psycopg2`

---

## Лицензия

MIT — делай что хочешь, но без гарантий. Используй только против целей, на которые у тебя есть разрешение.
