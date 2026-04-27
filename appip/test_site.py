# test_site.py - Простой тест работоспособности сайта
"""
Запуск: python test_site.py
"""

import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

BASE_URL = "http://localhost:8000"
TEST_DURATION = 20  # секунд
CONCURRENT_USERS = 3

stats = {
    'total': 0,
    'success': 0,
    'failed': 0,
    'times': []
}
lock = Lock()


def test_page(name, url, method='GET', data=None):
    """Тестирование одной страницы"""
    start = time.time()
    try:
        if method == 'GET':
            resp = requests.get(f"{BASE_URL}{url}", timeout=10)
        else:
            resp = requests.post(f"{BASE_URL}{url}", data=data, timeout=10)
        
        elapsed = time.time() - start
        
        with lock:
            stats['total'] += 1
            stats['times'].append(elapsed)
            if resp.status_code in [200, 302, 401]:
                stats['success'] += 1
                return True, elapsed
            else:
                stats['failed'] += 1
                print(f"   ❌ {name}: HTTP {resp.status_code} ({elapsed:.2f}s)")
                return False, elapsed
    except Exception as e:
        elapsed = time.time() - start
        with lock:
            stats['total'] += 1
            stats['failed'] += 1
            stats['times'].append(elapsed)
        print(f"   ❌ {name}: {str(e)[:50]}")
        return False, elapsed


def run_user(user_id):
    """Сценарий одного пользователя"""
    print(f"   👤 Пользователь {user_id} начал")
    
    # Страницы для тестирования
    pages = [
        ("Главная", "/"),
        ("Товары", "/products/"),
        ("Корзина", "/cart/"),
        ("Профиль", "/profile/"),
        ("Избранное", "/wishlist/"),
        ("Заказы", "/orders/"),
        ("API категории", "/api/categories/"),
        ("API типы", "/api/product-types/"),
    ]
    
    for name, url in pages:
        test_page(name, url)
        time.sleep(0.3)
    
    # Добавление в корзину (тест POST)
    test_page("Добавление в корзину", "/cart/add/", "POST", 
              data={'product_id': 1, 'quantity': 1})
    
    print(f"   ✅ Пользователь {user_id} завершил")


def run_simple_test():
    """Простой тест"""
    print("\n" + "="*60)
    print("🔧 ПРОСТОЙ ТЕСТ")
    print("="*60)
    
    pages = [
        ("Главная", "/"),
        ("Товары", "/products/"),
        ("Корзина", "/cart/"),
        ("Профиль", "/profile/"),
        ("API категории", "/api/categories/"),
    ]
    
    for name, url in pages:
        success, elapsed = test_page(name, url)
        if success:
            print(f"   ✅ {name}: {elapsed:.2f}s")
    
    print("\n" + "="*60)


def run_load_test():
    """Нагрузочный тест"""
    print("\n" + "="*60)
    print(f"🚀 НАГРУЗОЧНЫЙ ТЕСТ ({CONCURRENT_USERS} пользователей, {TEST_DURATION} сек)")
    print("="*60)
    
    # Проверка доступности
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        if resp.status_code != 200:
            print("❌ Сайт недоступен! Запустите: docker-compose up -d")
            return
        print("✅ Сайт доступен")
    except:
        print("❌ Сайт недоступен! Запустите: docker-compose up -d")
        return
    
    print(f"\n🔄 Запуск {CONCURRENT_USERS} пользователей...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(run_user, i) for i in range(CONCURRENT_USERS)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"   ⚠️ Ошибка: {e}")
    
    elapsed = time.time() - start_time
    
    # Статистика
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ")
    print("="*60)
    print(f"   Всего запросов: {stats['total']}")
    if stats['total'] > 0:
        print(f"   Успешно: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        print(f"   Ошибок: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    
    if stats['times']:
        print(f"\n⏱️ Время ответа:")
        print(f"   Среднее: {sum(stats['times'])/len(stats['times']):.2f}s")
        print(f"   Минимум: {min(stats['times']):.2f}s")
        print(f"   Максимум: {max(stats['times']):.2f}s")
    
    print(f"\n✅ Тест завершен за {elapsed:.1f} сек")
    print("="*60)


def test_db():
    """Тест подключения к БД (через API)"""
    print("\n" + "="*60)
    print("🗄️ ТЕСТ БД (через API)")
    print("="*60)
    
    try:
        # Проверяем API, которые работают с БД
        resp = requests.get(f"{BASE_URL}/api/categories/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ API категорий работает: {len(data)} категорий")
        else:
            print(f"   ⚠️ API категорий: HTTP {resp.status_code}")
        
        resp = requests.get(f"{BASE_URL}/api/product-types/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ API типов товаров работает: {len(data)} типов")
        else:
            print(f"   ⚠️ API типов товаров: HTTP {resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--simple', action='store_true', help='Простой тест')
    parser.add_argument('--load', action='store_true', help='Нагрузочный тест')
    parser.add_argument('--db', action='store_true', help='Тест БД')
    parser.add_argument('--users', type=int, default=3, help='Количество пользователей')
    parser.add_argument('--duration', type=int, default=20, help='Длительность (сек)')
    
    args = parser.parse_args()
    
    if args.users:
        CONCURRENT_USERS = args.users
    if args.duration:
        TEST_DURATION = args.duration
    
    if args.simple:
        run_simple_test()
    elif args.load:
        run_load_test()
    elif args.db:
        test_db()
    else:
        run_simple_test()
        test_db()
        run_load_test()