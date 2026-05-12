#!/bin/bash
set -e

echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ"

# ============================================
# 🔧 НАСТРОЙКА ПРАВ НА ПАПКУ MEDIA
# ============================================
echo "🔧 Настройка прав на папки..."

# Проверяем, примонтирован ли volume
if mountpoint -q /app/media 2>/dev/null; then
    echo "✅ Volume примонтирован в /app/media"
else
    echo "⚠️ Volume НЕ примонтирован, создаем обычную папку"
    mkdir -p /app/media
fi

# Создаем папки с проверкой прав
for dir in products temp avatars; do
    if [ -d "/app/media/$dir" ]; then
        echo "📁 Папка /app/media/$dir уже существует"
    else
        mkdir -p "/app/media/$dir" 2>/dev/null || {
            echo "⚠️ Не могу создать /app/media/$dir, пробуем с sudo"
            sudo mkdir -p "/app/media/$dir" 2>/dev/null || true
        }
    fi
done

# Даем максимальные права
chmod -R 777 /app/media 2>/dev/null || {
    echo "⚠️ Не могу изменить права, пробуем с sudo"
    sudo chmod -R 777 /app/media 2>/dev/null || true
}

echo "📁 Содержимое /app/media:"
ls -la /app/media/ 2>/dev/null || echo "Не удалось прочитать"
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
EOF

echo "📁 Собираем статику..."
python manage.py collectstatic --noinput

echo "🚀 Запуск Gunicorn на порту ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} buytovar.wsgi:application