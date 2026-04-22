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

## Шаг 4. Регистрация на PythonAnywhere

- [pythonanywhere.com](https://www.pythonanywhere.com)
- `Create a Beginner account` (бесплатно, **без карты**)
- Придумай username — он станет частью URL (`username.pythonanywhere.com`)

---

## Шаг 5. Настройка на PythonAnywhere

### 5.1 Открываем Bash-консоль
- Вверху нажми **Consoles**
- Нажми **Bash**

### 5.2 Копируем код с GitHub
Вставь в консоль (замени `bogdan` на свой GitHub username):

```bash
git clone https://github.com/bogdan/fc-mobile-bot.git fcbot
cd fcbot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5.3 Создаем .env файл
- Перейди во вкладку **Files**
- Слева кликни `fcbot` → `New file`
- Назови `.env` (с точкой!)
- Вставь и сохрани:

```
BOT_TOKEN=твой_токен_от_BotFather
ADMIN_IDS=твой_telegram_id
WEBAPP_URL=https://твой_юзернейм.pythonanywhere.com
```

### 5.4 Создаем Web App
- Вверху нажми **Web**
- Нажми `Add a new web app`
- `Next` → `Flask` → `Python 3.11` → `Next`

### 5.5 Настраиваем WSGI
- На странице Web найди раздел **Code**
- Нажми ссылку `WSGI configuration file` (что-то вроде `/var/www/username_pythonanywhere_com_wsgi.py`)
- **Удали всё** из файла и вставь:

```python
import sys
path = '/home/ТВОЙ_ЮЗЕРНЕЙМ/fcbot'
if path not in sys.path:
    sys.path.insert(0, path)
from main import app as application
import main
main._set_webhook()
```

- Замени `ТВОЙ_ЮЗЕРНЕЙМ` на твой username с PythonAnywhere
- Сохрани (зелёная кнопка)

### 5.6 Перезагружаем
- Верись на вкладку **Web**
- Нажми зелёную кнопку **Reload** (рядом с именем сайта)
- Жди 10-20 секунд

### 5.7 Проверяем
- Открой в новой вкладке: `https://твой_юзернейм.pythonanywhere.com`
- Должна открыться страница бота

---

## Шаг 6. Завершаем настройку бота

В BotFather:
- `Bot Settings` → `Menu Button`
- Поменяй URL на: `https://твой_юзернейм.pythonanywhere.com`

Добавь бота в группу, дай права администратора.

---

## Использование бота

### Для админа
1. Напиши боту в личку `/start`
2. Нажми `⚙️ Админ`
3. `Создать турнир` → введи: `FC Mobile Cup, 2` (название и кол-во групп)
4. `Открыть регистрацию` — бот пишет сообщение в группу
5. Жди пока игроки ответят `+ник`
6. `Закрыть и жеребьевка` — бот делит на группы

### Для игроков
- Ответь `+ProPlayer123` на сообщение сбора
- Пиши боту в личку: `с кем я играю`
- После матча в группу: `@user1 выиграл 3-0 @user2`

### WebApp
- Нажми кнопку `📊 Мои матчи` в меню бота
- Вкладки: таблицы, свои матчи, оставшиеся игры

---

## Структура проекта

```
.
├── bot.py              # Telegram-бот (команды, регистрация, результаты)
├── tournament.py       # Логика round-robin групп и подсчета очков
├── models.py           # База данных (SQLite через SQLAlchemy)
├── main.py             # Flask сервер + webhook + WebApp API
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
