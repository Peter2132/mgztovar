#!/bin/bash
set -e

echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ"

# Создаем папку если volume не примонтирован
mkdir -p /app/media 2>/dev/null || true

# ДАЕМ ПРАВА 777 НА ВСЮ ПАПКУ MEDIA
echo "🔧 Даю права 777 на /app/media..."
chmod 777 /app/media 2>/dev/null || {
    echo "⚠️ chmod не сработал, пробуем sudo..."
    sudo chmod 777 /app/media 2>/dev/null || true
}

# Создаем подпапки
mkdir -p /app/media/products
mkdir -p /app/media/temp

# Даем права 777 на все подпапки
chmod -R 777 /app/media 2>/dev/null || sudo chmod -R 777 /app/media 2>/dev/null || true

echo "📁 Права на /app/media:"
ls -la /app/ | grep media
ls -la /app/media/

echo "📦 Выполняем миграции..."
python manage.py migrate --noinput

echo "👤 Создание ролей и администратора..."
python manage.py shell << EOF
from appip.models import Users, Roles

if not Roles.objects.exists():
    Roles.objects.create(id_role=1, role_name='Администратор')
    Roles.objects.create(id_role=2, role_name='Пользователь')
    Roles.objects.create(id_role=3, role_name='Менеджер')
    print('✅ Роли созданы')

if not Users.objects.exists():
    admin_role = Roles.objects.filter(id_role=1).first()
    if admin_role:
        admin = Users.objects.create(
            login='admin@admin.com',
            firstname='Admin',
            surname='Admin',
            role=admin_role,
            is_active=True,
            balance=0
        )
        admin.set_password('admin123')
        admin.save()
        print('✅ Администратор создан')
EOF

echo "📁 Собираем статику..."
python manage.py collectstatic --noinput

echo "🚀 Запуск на порту ${PORT:-8080}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} buytovar.wsgi:application