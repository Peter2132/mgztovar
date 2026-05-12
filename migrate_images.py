import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import sys

# Загрузка .env
load_dotenv()

# Получаем ключи из переменных окружения
CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
API_KEY = os.environ.get('CLOUDINARY_API_KEY')
API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# Проверка наличия ключей
if not all([CLOUD_NAME, API_KEY, API_SECRET]):
    print("❌ ОШИБКА: Не найдены переменные окружения!")
    print("\nДобавьте в файл .env следующие переменные:")
    print("CLOUDINARY_CLOUD_NAME=your_cloud_name")
    print("CLOUDINARY_API_KEY=your_api_key")
    print("CLOUDINARY_API_SECRET=your_api_secret")
    print("\nИли установите их вручную:")
    CLOUD_NAME = input("Cloud Name: ").strip()
    API_KEY = input("API Key: ").strip()
    API_SECRET = input("API Secret: ").strip()

# Настройка Cloudinary
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

print(f"✅ Cloudinary настроен с cloud_name: {CLOUD_NAME}\n")

# Путь к папке с картинками
media_path = 'media/products'

if not os.path.exists(media_path):
    print(f"❌ Папка {media_path} не найдена!")
    sys.exit(1)

# Получаем список файлов
files = [f for f in os.listdir(media_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]

if not files:
    print(f"❌ В папке {media_path} нет изображений!")
    sys.exit(1)

print(f"📁 Найдено {len(files)} изображений\n")

success_count = 0
error_count = 0

for filename in files:
    file_path = os.path.join(media_path, filename)
    public_id = filename.split('.')[0]
    
    print(f"🔼 Загрузка: {filename}...")
    
    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder="products",
            public_id=public_id,
            overwrite=True
        )
        
        print(f"   ✅ Загружено: {result['secure_url']}")
        print(f"   📍 Public ID: {result['public_id']}")
        success_count += 1
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        error_count += 1
    
    print()

print("=" * 50)
print(f"📊 ИТОГО: Успешно: {success_count}, Ошибок: {error_count}")
print("=" * 50)