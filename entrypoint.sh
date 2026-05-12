#!/bin/bash
set -e

echo "⏳ Ожидание PostgreSQL..."

# ИСПРАВЛЕННАЯ КОМАНДА pg_isready
until pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER"; do
  echo "PostgreSQL не готов, ждем 2 секунды..."
  sleep 2
done
echo "✅ PostgreSQL готов!"

echo "📦 Выполняем миграции..."
python manage.py migrate --noinput

echo "👤 Создание ролей и администратора..."
python manage.py shell << EOF
from appip.models import Users, Roles

# Создаем роли
if not Roles.objects.exists():
    Roles.objects.create(id_role=1, role_name='Администратор')
    Roles.objects.create(id_role=2, role_name='Пользователь')
    Roles.objects.create(id_role=3, role_name='Менеджер')
    print('✅ Роли созданы')

# Создаем админа если нет пользователей
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
    else:
        print('⚠️ Роль администратора не найдена')
else:
    print('✅ Пользователи уже существуют')
EOF

echo "📁 Собираем статику..."
python manage.py collectstatic --noinput

echo "🚀 Запуск Gunicorn на порту ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} buytovar.wsgi:application