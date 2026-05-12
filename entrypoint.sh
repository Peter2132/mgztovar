#!/bin/bash
set -e

echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ"

# ЖДЕМ, ПОКА RAILWAY ПРИМОНТИРУЕТ VOLUME
echo "⏳ Ждем монтирования volume..."
sleep 5

# ============================================
# ПРОВЕРЯЕМ И СОЗДАЕМ ПАПКИ (ПОСЛЕ МОНТИРОВАНИЯ)
# ============================================
echo "🔧 Настройка прав на папки..."

# Проверяем, существует ли папка /app/media
if [ ! -d "/app/media" ]; then
    echo "❌ Папка /app/media не существует! Создаем..."
    mkdir -p /app/media
fi

# Создаем подпапки
mkdir -p /app/media/products 2>/dev/null || {
    echo "⚠️ Не могу создать папку, пробуем с sudo..."
    sudo mkdir -p /app/media/products 2>/dev/null || {
        echo "❌ КРИТИЧЕСКАЯ ОШИБКА: не могу создать /app/media/products"
        echo "📁 Текущее содержимое /app:"
        ls -la /app/
        echo "📁 Текущий пользователь:"
        whoami
        id
    }
}

# Даем права 777
chmod -R 777 /app/media 2>/dev/null || {
    echo "⚠️ chmod не сработал, пробуем sudo..."
    sudo chmod -R 777 /app/media 2>/dev/null || true
}

echo "📁 Содержимое /app/media:"
ls -la /app/media/ 2>/dev/null || echo "Не удалось прочитать"

# ПРОВЕРКА: можем ли мы записать файл
echo "test" > /app/media/test.txt 2>/dev/null && {
    echo "✅ Запись в /app/media РАБОТАЕТ!"
    rm /app/media/test.txt
} || {
    echo "❌ Запись в /app/media НЕ РАБОТАЕТ!"
    echo "🔍 Детальная информация:"
    ls -la /app/
    df -h
}
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
        print('✅ Администратор создан')
EOF

echo "📁 Собираем статику..."
python manage.py collectstatic --noinput

echo "🚀 Запуск на порту ${PORT:-8080}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} buytovar.wsgi:application