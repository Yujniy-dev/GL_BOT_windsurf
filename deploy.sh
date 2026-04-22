#!/bin/bash
# Скрипт для обновления на PythonAnywhere
# Копируй и вставь в Bash-консоль целиком

echo "=== Обновление кода ==="
cd ~/fcbot || exit

git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "Git pull пропущен"

source venv/bin/activate
pip install -r requirements.txt

# Перезагружаем Web App (PythonAnywhere увидит изменение WSGI)
touch /var/www/$(whoami)_pythonanywhere_com_wsgi.py

echo "=== Готово! Web App перезагрузится автоматически ==="
