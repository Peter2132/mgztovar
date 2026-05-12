#!/bin/bash
set -e

echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ (БЕЗ ПРОВЕРКИ БД)"

# Просто спим 5 секунд для уверенности
sleep 5

echo "📦 Миграции..."
python manage.py migrate --noinput

echo "👤 Создание ролей..."
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

echo "📁 Статика..."
python manage.py collectstatic --noinput

echo "🚀 Запуск на порту ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} buytovar.wsgi:application