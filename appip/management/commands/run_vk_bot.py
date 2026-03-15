# appip/management/commands/run_vk_bot.py
from django.core.management.base import BaseCommand
from appip.vk_bot import run_vk_bot

class Command(BaseCommand):
    help = 'Запуск VK бота'

    def handle(self, *args, **options):
        self.stdout.write('Запуск VK бота...')
        run_vk_bot()