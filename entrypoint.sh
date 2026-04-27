#!/bin/bash
set -e

echo "⏳ Ожидание готовности PostgreSQL..."
until pg_isready -h db -U ${DB_USER} -d ${DB_NAME}; do
  sleep 2
done
echo "✅ PostgreSQL готов!"

# Проверяем, есть ли бэкап для восстановления
if [ -f "/app/backups/auto_restore.zip" ] && [ -n "$(ls -A /app/backups/auto_restore.zip 2>/dev/null)" ]; then
    echo "🔄 Найден бэкап для автоматического восстановления..."
    python manage.py migrate --noinput || true
    python /app/restore_backup.py /app/backups/auto_restore.zip
    # Переименовываем, чтобы не восстанавливать повторно
    mv /app/backups/auto_restore.zip /app/backups/restored_$(date +%Y%m%d_%H%M%S).zip
else
    echo "📦 Выполняем миграции..."
    python manage.py migrate --noinput
fi

# Создаем суперпользователя если его нет
echo "👤 Проверка суперпользователя..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin@admin.com', 'admin123')
    print('✅ Суперпользователь создан')
"

echo "📁 Собираем статику..."
python manage.py collectstatic --noinput

echo "🚀 Запуск Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 buytovar.wsgi:application