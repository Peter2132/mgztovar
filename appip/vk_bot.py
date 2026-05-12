# appip/vk_bot.py
import logging
import re
import os
import django
import requests
import random
import time
from threading import Thread
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buytovar.settings')
django.setup()

from django.conf import settings
from .models import Users, Messages, Chats, TelegramManager

logger = logging.getLogger(__name__)

# =====================================================
# ================= VK CONFIG =========================
# =====================================================

VK_API_VERSION = '5.131'
VK_GROUP_TOKEN = settings.VK_GROUP_TOKEN
VK_GROUP_ID = settings.VK_GROUP_ID

VK_API_URL = 'https://api.vk.com/method/'

class VKBot:
    def __init__(self, token, group_id):
        self.token = token
        self.group_id = int(group_id) if group_id else None
        self.ts = None
        self.server = None
        self.key = None
        self.running = True
        
    def api_request(self, method, params=None):
        """Универсальный метод для вызова VK API"""
        if params is None:
            params = {}
        params.update({
            'access_token': self.token,
            'v': VK_API_VERSION
        })
        
        try:
            response = requests.get(f"{VK_API_URL}{method}", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"VK API Error: {data['error']}")
                return None
            return data.get('response')
        except Exception as e:
            logger.error(f"VK API Request Error: {e}")
            return None
    
    def get_long_poll_server(self):
        """Получаем сервер для Long Poll"""
        response = self.api_request('groups.getLongPollServer', {
            'group_id': self.group_id
        })
        if response:
            self.server = response['server']
            self.key = response['key']
            self.ts = response['ts']
            logger.info(f"Long Poll server obtained: {self.server}")
            return True
        return False
    
    def listen(self):
        """Основной цикл прослушивания сообщений"""
        if not self.get_long_poll_server():
            logger.error("Failed to get Long Poll server")
            return
        
        while self.running:
            try:
                url = f"{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=25"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'failed' in data:
                    failed = data['failed']
                    if failed == 1:
                        self.ts = data['ts']
                    elif failed in [2, 3]:
                        self.get_long_poll_server()
                    continue
                
                self.ts = data['ts']
                
                for update in data.get('updates', []):
                    self.process_update(update)
                    
            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                logger.error(f"Long Poll error: {e}")
                time.sleep(5)
    
    def process_update(self, update):
        """Обработка входящего обновления"""
        # Игнорируем события печати (message_typing_state)
        if update.get('type') == 'message_typing_state':
            return
            
        if update.get('type') == 'message_new':
            message_data = update.get('object', {}).get('message', {})
            if message_data:
                self.handle_message(message_data)
    
    def handle_message(self, message):
        """Обработка входящего сообщения"""
        try:
            # Извлекаем данные сообщения (конвертируем в числа где нужно)
            peer_id = message.get('peer_id')
            from_id = message.get('from_id')
            text = message.get('text', '')
            
            # Конвертируем ID в int если пришло как строка
            if from_id and isinstance(from_id, str):
                from_id = int(from_id)
            if peer_id and isinstance(peer_id, str):
                peer_id = int(peer_id)
            
            logger.info(f"📨 Получено сообщение: from_id={from_id}, text='{text}'")
            
            # Игнорируем сообщения без отправителя
            if from_id is None:
                return
                
            # Игнорируем сообщения от самого бота
            if from_id < 0 or (self.group_id and from_id == -self.group_id):
                return
            
            # Получаем информацию о пользователе
            user_info = self.get_user_info(from_id)
            if not user_info:
                logger.warning(f"Не удалось получить информацию о пользователе {from_id}")
                return
            
            vk_username = user_info.get('screen_name')
            first_name = user_info.get('first_name', '')
            
            logger.info(f"👤 Пользователь: {first_name}, username: @{vk_username}")
            
            # Проверяем команду /start
            if text == '/start' or text.lower() == 'начать':
                self.handle_start_command(peer_id, from_id, vk_username, user_info)
                return
            
            # Ищем менеджера в БД по VK username
            try:
                manager = Users.objects.get(
                    login=vk_username,
                    role_id=3,
                    is_active=True
                )
                
                logger.info(f"✅ Менеджер найден: {manager.firstname} {manager.surname}")
                
                # Обновляем или создаем запись менеджера
                tg_manager, created = TelegramManager.objects.update_or_create(
                    manager=manager,
                    defaults={
                        'vk_peer_id': peer_id,
                        'vk_username': vk_username,
                        'is_active': True
                    }
                )
                
                # Это ответ менеджера
                if message.get('reply_message'):
                    self.handle_manager_reply(message, manager)
                else:
                    self.handle_command(message, manager)
                    
            except Users.DoesNotExist:
                logger.info(f"Менеджер с логином '{vk_username}' не найден")
                self.handle_user_message(message, from_id, vk_username, text)
            except Exception as e:
                logger.error(f"Ошибка при поиске менеджера: {e}")
                
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
    
    def handle_start_command(self, peer_id, from_id, vk_username, user_info):
        """Обработка команды /start для регистрации менеджера"""
        try:
            manager = Users.objects.get(
                login=vk_username,
                role_id=3,
                is_active=True
            )
            
            TelegramManager.objects.update_or_create(
                manager=manager,
                defaults={
                    'vk_peer_id': peer_id,
                    'vk_username': vk_username,
                    'is_active': True
                }
            )
            
            first_name = user_info.get('first_name', '')
            response_text = (
                f"✅ Здравствуйте, {first_name}!\n"
                f"Вы зарегистрированы как менеджер.\n"
                f"Теперь вы будете получать уведомления о новых сообщениях.\n\n"
                f"Команды:\n"
                f"/chats - список ваших чатов\n"
                f"/help - помощь"
            )
            
            self.send_message(peer_id, response_text)
            logger.info(f"Менеджер {vk_username} зарегистрирован")
            
        except Users.DoesNotExist:
            error_text = (
                f"❌ Менеджер с username @{vk_username} не найден.\n"
                f"Убедитесь, что:\n"
                f"1. Вы зарегистрированы на сайте\n"
                f"2. Ваш логин на сайте совпадает с @{vk_username}\n"
                f"3. Вам назначена роль 'Менеджер'"
            )
            self.send_message(peer_id, error_text)
        except Exception as e:
            logger.error(f"Start command error: {e}")
            self.send_message(peer_id, "❌ Ошибка регистрации")
    
    def get_user_info(self, user_id):
        """Получаем информацию о пользователе VK"""
        if not user_id:
            return None
            
        response = self.api_request('users.get', {
            'user_ids': user_id,
            'fields': 'screen_name,first_name,last_name'
        })
        if response and len(response) > 0:
            return response[0]
        return None
    
    def send_message(self, peer_id, text, reply_to=None):
        """Отправка сообщения"""
        if not peer_id:
            logger.error("Нет peer_id для отправки сообщения")
            return None
            
        random_id = random.randint(-2**31, 2**31 - 1)
        params = {
            'peer_id': peer_id,
            'message': text,
            'random_id': random_id,
            'access_token': self.token,
            'v': VK_API_VERSION
        }
        
        if reply_to:
            params['reply_to'] = reply_to
        
        try:
            response = requests.post(f"{VK_API_URL}messages.send", data=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"VK API Error: {data['error']}")
                return None
            return data.get('response')
        except Exception as e:
            logger.error(f"VK send error: {e}")
            return None
    
    def handle_manager_reply(self, message, manager):
        """Менеджер отвечает пользователю - создает сообщение в чате сайта"""
        reply_message = message.get('reply_message')
        if not reply_message:
            return
            
        original_text = reply_message.get('text', '')
        
        # Ищем ID чата в тексте оригинального сообщения
        match = re.search(r'Чат ID: (\d+)', original_text)
        if not match:
            self.send_message(
                message['peer_id'],
                "❌ Не удалось определить ID чата",
                reply_to=message.get('id')
            )
            return
        
        chat_id = int(match.group(1))
        reply_text = message.get('text', '')
        
        if not reply_text.strip():
            self.send_message(
                message['peer_id'],
                "❌ Сообщение не может быть пустым",
                reply_to=message.get('id')
            )
            return
        
        try:
            # Проверяем чат
            chat = Chats.objects.get(id_chat=chat_id)
            
            # Создаем сообщение в БД
            new_message = Messages.objects.create(
                chat_id=chat_id,
                sender_id=manager.id_user,
                message_text=reply_text,
                sent_at=timezone.now()
            )
            
            # Обновляем время
            chat.last_message_at = timezone.now()
            chat.save()
            
            self.send_message(
                message['peer_id'],
                f"✅ Ответ отправлен в чат #{chat_id}",
                reply_to=message.get('id')
            )
            
            logger.info(f"Ответ менеджера отправлен в чат #{chat_id}")
            
        except Chats.DoesNotExist:
            self.send_message(
                message['peer_id'],
                f"❌ Чат #{chat_id} не найден",
                reply_to=message.get('id')
            )
        except Exception as e:
            logger.error(f"Error sending manager reply: {e}")
            self.send_message(
                message['peer_id'],
                f"❌ Ошибка: {str(e)}",
                reply_to=message.get('id')
            )
    
    def handle_command(self, message, manager):
        """Обработка команд от менеджера"""
        text = message.get('text', '').lower().strip()
        peer_id = message.get('peer_id')
        
        if text == '/chats' or text == 'чаты' or text == 'chats':
            self.show_chats(peer_id, manager, message.get('id'))
        elif text == '/help' or text == 'помощь' or text == 'help':
            self.send_message(
                peer_id,
                "📋 Доступные команды:\n"
                "/chats - список ваших активных чатов\n"
                "/help - это сообщение",
                reply_to=message.get('id')
            )
    
    def show_chats(self, peer_id, manager, reply_to_id):
        """Показать активные чаты менеджера"""
        try:
            chats = Chats.objects.filter(
                seller_id=manager.id_user,
                is_active=True
            ).select_related('buyer', 'product').order_by('-last_message_at')[:10]
            
            if not chats.exists():
                self.send_message(
                    peer_id,
                    "📭 У вас нет активных чатов.",
                    reply_to=reply_to_id
                )
                return
            
            response = "📋 Ваши активные чаты:\n\n"
            
            for chat in chats:
                last_msg = Messages.objects.filter(chat=chat).order_by('-sent_at').first()
                last_msg_time = last_msg.sent_at.strftime('%d.%m %H:%M') if last_msg else 'Нет сообщений'
                
                unread_count = Messages.objects.filter(
                    chat=chat,
                    sender_id=chat.buyer_id,
                    is_read=False
                ).count()
                
                unread_mark = f" [+{unread_count}]" if unread_count > 0 else ""
                
                response += (
                    f"🆔 Чат ID: {chat.id_chat}\n"
                    f"👤 Покупатель: {chat.buyer.login}\n"
                    f"📦 Товар: {chat.product.title if chat.product else 'Общий чат'}\n"
                    f"🕒 Последнее: {last_msg_time}{unread_mark}\n"
                    f"----------------------\n"
                )
            
            response += "\n💬 Чтобы ответить, ответьте на это сообщение"
            
            self.send_message(peer_id, response, reply_to=reply_to_id)
            logger.info(f"Список чатов отправлен менеджеру {manager.login}")
            
        except Exception as e:
            logger.error(f"Error showing chats: {e}")
            self.send_message(
                peer_id,
                "❌ Ошибка при загрузке чатов",
                reply_to=reply_to_id
            )
    
    def handle_user_message(self, message, from_id, vk_username, text):
        """Обычный пользователь пишет сообщение - создаем чат в БД"""
        peer_id = message.get('peer_id')
        
        try:
            user = Users.objects.get(login=vk_username, is_active=True)
            
            # Здесь нужно создать чат и сообщение в БД сайта
            # Для этого нужно найти или создать чат между пользователем и менеджером
            
            # Ищем менеджера (можно назначить главного менеджера)
            manager = Users.objects.filter(role_id=3, is_active=True).first()
            
            if not manager:
                self.send_message(
                    peer_id,
                    "❌ В системе нет активных менеджеров. Попробуйте позже."
                )
                return
            
            # Создаем или находим чат
            chat, created = Chats.objects.get_or_create(
                buyer=user,
                seller=manager,
                defaults={'is_active': True}
            )
            
            # Создаем сообщение
            new_message = Messages.objects.create(
                chat=chat,
                sender=user,
                message_text=text,
                sent_at=timezone.now()
            )
            
            # Обновляем время
            chat.last_message_at = timezone.now()
            chat.save()
            
            # Отправляем подтверждение пользователю
            self.send_message(
                peer_id,
                f"✅ Ваше сообщение отправлено менеджеру.\n"
                f"Ожидайте ответа. Номер чата: #{chat.id_chat}"
            )
            
            # Здесь можно добавить уведомление менеджеру через Telegram/VK
            logger.info(f"Создан чат #{chat.id_chat} для пользователя {user.login}")
            
        except Users.DoesNotExist:
            self.send_message(
                peer_id,
                "❌ Вы не зарегистрированы в системе.\n"
                f"Ваш VK username (@{vk_username}) должен совпадать с логином на сайте."
            )
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            self.send_message(peer_id, "❌ Ошибка при обработке сообщения")
    
    def stop(self):
        """Остановка бота"""
        self.running = False
        logger.info("VK bot stopping...")


def run_vk_bot():
    """Функция для запуска VK бота"""
    if not VK_GROUP_TOKEN or not VK_GROUP_ID:
        logger.error("VK_GROUP_TOKEN or VK_GROUP_ID not set in settings")
        return
        
    bot = VKBot(VK_GROUP_TOKEN, VK_GROUP_ID)
    
    try:
        logger.info("🚀 Запуск VK бота...")
        bot.listen()
    except KeyboardInterrupt:
        logger.info("👋 Остановка VK бота...")
        bot.stop()
    except Exception as e:
        logger.error(f"💥 VK Bot error: {e}")
    finally:
        logger.info("VK bot finished")

if __name__ == "__main__":
    run_vk_bot()