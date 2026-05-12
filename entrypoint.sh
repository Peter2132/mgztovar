#!/bin/bash
set -e

echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ"

# Ожидание готовности PostgreSQL
echo "⏳ Ожидание PostgreSQL..."
until pg_isready -h $DB_HOST -U $DB_USER -d $DB_NAME; do
  echo "PostgreSQL не готов, ждем 2 секунды..."
  sleep 2
done
echo "✅ PostgreSQL готов!"

# ============================================
# 🔧 НАСТРОЙКА ПРАВ НА ПАПКУ MEDIA
# ============================================
echo "🔧 Настройка прав на папки..."

# Создаем папки если их нет
mkdir -p /app/media/products
mkdir -p /app/media/temp
mkdir -p /app/media/avatars

# Исправляем права (Railway использует пользователя с UID 1000)
chown -R 1000:1000 /app/media 2>/dev/null || true
chmod -R 755 /app/media
chmod -R 777 /app/media/products
chmod -R 777 /app/media/temp
chmod -R 777 /app/media/avatars

# Проверяем права
echo "📁 Права на папки:"
ls -la /app/media/
echo "✅ Права настроены"
# ============================================

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
else:
    print('✅ Роли уже существуют')

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
        print('✅ Администратор создан (admin@admin.com / admin123)')
    else:
        print('⚠️ Роль администратора не найдена')
else:
    print('✅ Пользователи уже существуют')
EOF

echo "📁 Собираем статику..."
python manage.py collectstatic --noinput

echo "🚀 Запуск Gunicorn на порту ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} buytovar.wsgi:application