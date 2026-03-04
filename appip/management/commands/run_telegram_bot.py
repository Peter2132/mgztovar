# appip/management/commands/run_telegram_bot.py
import asyncio
import logging
import os
import sys
import django
from django.core.management.base import BaseCommand
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buytovar.settings')  # Укажите имя вашего проекта
django.setup()

# Импортируем после настройки Django
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем наш бот
from appip.telegram_bot import dp, bot

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запуск Telegram бота для менеджеров'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))
        
        async def main():
            await dp.start_polling(bot)
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Бот остановлен'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {str(e)}'))