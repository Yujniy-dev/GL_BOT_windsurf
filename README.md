# FC Mobile Tournament Bot (H2H) — Полный гайд с нуля

Telegram-бот для проведения групповых турниров по FC Mobile (H2H). Каждый с каждым по 2 матча в группах.

---

## Шаг 1. Создаем бота в Telegram

1. Найди `@BotFather` в Telegram, напиши `/newbot`
2. Придумай имя и username (например `FC_Mobile_Tournament_Bot`)
3. **Сохрани токен** который даст BotFather (`123456789:ABC...`)

### Настройка WebApp
- В BotFather: `Bot Settings` → `Menu Button` → `Configure menu button`
- URL пока любой (поменяешь после деплоя)

### Отключить privacy (обязательно!)
- `Bot Settings` → `Group Privacy` → `Turn off`

---

## Шаг 2. Узнай свой Telegram ID

Найди `@userinfobot` в Telegram — он покажет твой ID (например `123456789`).

---

## Шаг 3. Заливаем код на GitHub

### 3.1 Регистрация
- [github.com](https://github.com) → `Sign up`
- Подтверди email в почте

### 3.2 Создаем репозиторий
- Вверху справа нажми `+` → `New repository`
- Repository name: `fc-mobile-bot`
- Нажми `Create repository`

### 3.3 Устанавливаем GitHub Desktop
- Скачай: [desktop.github.com](https://desktop.github.com)
- Установи, залогинься
- `File` → `Add local repository`
- Выбери папку проекта: `C:\Users\Богдан\Desktop\Youtube_FC\GL_BOT_windsurf`
- Если появится ошибка **"This directory does not appear to be a Git repository"** — нажми синюю ссылку **"create a repository here instead"**
- В открывшемся окне нажми **Create repository**
- Потом нажми **Publish repository** (кнопка сверху справа)
- **Убери галочку "Keep this code private"**
- Нажми `Publish repository`

Готово, код на GitHub!

---

## Шаг 4. Регистрация на Render

**Важно:** PythonAnywhere free tier блокирует Telegram API. Используем **Render** — бесплатно, без карты.

- Зайди на [render.com](https://render.com)
- Нажми `Get Started For Free`
- Регистрация через **GitHub** (самый простой способ)
- Подтверди email

---

## Шаг 5. Деплой на Render

### 5.1 Создаем Web Service
1. В Dashboard нажми `New +` → `Web Service`
2. Выбери свой репозиторий `fc-mobile-bot`
3. Настройки:
   - **Name**: `fc-mobile-bot` (или любое)
   - **Region**: Frankfurt (EU Central)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python setup_webhook.py && gunicorn main:app --bind 0.0.0.0:$PORT`
4. Нажми `Create Web Service`

### 5.2 Добавляем переменные окружения
1. На странице сервиса перейди во вкладку **Environment**
2. Добавь переменные (кнопка `Add Environment Variable`):

| Key | Value |
|---|---|
| `BOT_TOKEN` | `твой_токен_от_BotFather` |
| `ADMIN_IDS` | `твой_telegram_id` |
| `WEBAPP_URL` | `https://fc-mobile-bot-xxx.onrender.com` (подставь свой URL из Render) |
| `OCR_API_KEY` | `твой_ключ_с_ocr.space` (для распознавания скриншотов) |
| `DATABASE_URL` | `postgresql://...` (см. Шаг 5.2.1 ниже) |

Получи бесплатный OCR ключ на [ocr.space/ocrapi/freekey](https://ocr.space/ocrapi/freekey) — просто введи email, ключ придёт в письме. 25000 запросов/месяц бесплатно.

### 5.2.1 Neon Postgres (постоянная БД)

**Важно:** Render free tier стирает файловую систему при каждом деплое. Без внешней БД бот забудет все турниры и группы. Подключаем Neon — бесплатно и навсегда.

1. Зайди на [neon.tech](https://neon.tech) → `Sign up` (через GitHub проще всего)
2. После регистрации откроется мастер создания проекта:
   - **Project name**: `fc-mobile-bot` (любое)
   - **Postgres version**: оставь по умолчанию (16+)
   - **Region**: Europe (Frankfurt) или ближайший
   - Нажми `Create project`
3. Откроется страница с **Connection string** (выглядит как `postgresql://user:pass@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require`)
4. Нажми **Copy** — скопируй всю строку
5. В Render → вкладка **Environment** → `Add Environment Variable`:
   - Key: `DATABASE_URL`
   - Value: вставь скопированную строку
   - `Save Changes`

Render автоматически пересоберёт сервис. В логах появится `Webhook set to ...` — всё готово.

**Готово!** Теперь БД живёт в Neon, а не на Render. Коммиты не стирают данные.

3. URL сервиса виден на странице Dashboard (например `https://fc-mobile-bot-abc123.onrender.com`)

### 5.3 Ждем деплой
- Render автоматически соберёт и запустит
- Во вкладке **Logs** будут зелёные строки — значит всё ок
- Когда увидишь `Webhook set to ...` — готово!

### 5.4 Проверяем
- Открой URL сервиса в браузере
- Должна открыться страница бота

---

## Шаг 6. Завершаем настройку бота

В BotFather:
- `Bot Settings` → `Menu Button`
- Поменяй URL на: `https://твой-url-с-render.onrender.com/app.html`
- Текст кнопки: `Мои матчи`

Добавь бота в группу, дай права администратора.

> **Note:** Render free tier "засыпает" через 15 минут неактивности. При любом сообщении в бота или открытии WebApp сервер мгновенно просыпается. Если нужен 100% uptime — рассмотри платный тариф ($7/мес) или [Railway](https://railway.app) ($5 кредитов/мес на free tier).

---

## Использование бота

### Для админа
1. Добавь бота в группу как **администратора** (важно!)
2. Напиши боту в личку `/start`
3. Нажми `⚙️ Админ`
4. `Создать турнир` → введи: `FC Mobile Cup, 2` (название и кол-во групп)
5. `Открыть регистрацию` → выбери группу из списка (бот пишет туда сбор)
6. Жди пока игроки ответят `+клубное_имя`
7. `Закрыть и жеребьевка` — бот проводит жеребьёвку **прямо в группе**

### Для игроков
- Ответь `+ClubName` на сообщение сбора — пиши **клубное имя как в FC Mobile** (например `+GL·Distra`)
- Пиши боту в личку: `с кем я играю` — список матчей
- Результат матча тремя способами:
  - **📸 Скриншот** (рекомендуется): пришли фото таблицы FC Mobile боту. Бот распознает счёт, сопоставит клубные имена — и если нашёл оба, результат сохранится автоматически. Если не уверен — предложит выбрать соперника кнопкой.
  - **Текст**: `@user1 выиграл 3-0 @user2` или `@user1 ничья 2-2 @user2`

### WebApp
- Нажми кнопку `📊 Мои матчи` в меню бота
- Вкладки: таблицы групп, свои матчи, оставшиеся игры

---

## Структура проекта

```
.
├── bot.py              # Telegram-бот (команды, регистрация, результаты)
├── tournament.py       # Логика round-robin групп и подсчета очков
├── models.py           # База данных (SQLite через SQLAlchemy)
├── main.py             # Flask сервер + webhook + WebApp API
├── ocr.py              # OCR скриншотов (OCR.space) + fuzzy match имён
├── setup_webhook.py    # Установка webhook при старте
├── config.py           # Настройки из .env
├── webapp/             # WebApp файлы
│   ├── index.html
│   ├── app.html
│   └── static/
│       ├── style.css
│       └── app.js
├── requirements.txt    # Python библиотеки
├── deploy.sh           # Скрипт обновления на сервере
├── .env.example        # Шаблон настроек
└── .gitignore
```

---

## Обновление кода

Если изменил код и залил на GitHub:
1. Открой Bash-консоль на PythonAnywhere
2. Вставь:

```bash
cd ~/fcbot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

3. Перейди во вкладку **Web** → нажми **Reload**

---

## Частые проблемы

| Проблема | Решение |
|---|---|
| Бот не отвечает в группе | Отключи Group Privacy в BotFather, дай боту админку в группе |
| WebApp не открывается | Проверь URL в BotFather и .env, нажми Reload на PythonAnywhere |
| Ошибка 502 | Проверь WSGI файл, убедись что пути правильные |
| Бот не видит результаты | Проверь что участники написали @username корректно |
| WebApp долго грузится | PythonAnywhere free засыпает после 3ч — первый запрос 15-30 секунд |

---

## Бесплатно навсегда?

PythonAnywhere Free:
- 24/7 с небольшим ограничением: после 3 часов без запросов приложение "засыпает"
- При любом запросе (сообщение в бота, открытие WebApp) мгновенно просыпается
- **Бот продолжает работать** через webhook — Telegram шлет запросы = бот всегда жив

Если нужен 100% uptime без сна — рассмотри Oracle Cloud Free Tier (требует карту для верификации, но 0$ списаний).
