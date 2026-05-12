import logging
import time
import requests
import random
import os
import django
from datetime import datetime
from django.conf import settings

# Настройка Django для работы вне веб-сервера
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buytovar.settings')
django.setup()

from appip.models import Users, Messages, Chats

logger = logging.getLogger(__name__)

VK_API_VERSION = '5.131'
VK_API_URL = 'https://api.vk.com/method/'

class VKBot:
    def __init__(self, token, group_id):
        self.token = token
        self.group_id = group_id
        self.ts = None
        self.server = None
        self.key = None
        self.running = True
        
    def api_request(self, method, params=None):
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
        response = self.api_request('groups.getLongPollServer', {
            'group_id': self.group_id
        })
        if response:
            self.server = response['server']
            self.key = response['key']
            self.ts = response['ts']
            logger.info(f"Long Poll server obtained")
            return True
        return False
    
    def send_vk_message(self, peer_id, text, reply_to=None):
        if not peer_id:
            return None
            
        random_id = random.randint(0, 2**31 - 1)
        
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
            logger.info(f"VK Message sent to {peer_id}")
            return data.get('response')
        except Exception as e:
            logger.error(f"VK send error: {e}")
            return None
    
    def find_user_by_vk_id(self, vk_id):
        """Найти пользователя по VK ID (по логину)"""
        try:
            # Пытаемся найти пользователя с логином как VK ID
            user = Users.objects.filter(login=str(vk_id)).first()
            if user:
                return user
            # Ищем по имени пользователя
            return None
        except Exception as e:
            logger.error(f"Find user error: {e}")
            return None
    
    def create_message_in_chat(self, from_id, text, chat_id=None):
        """Создать сообщение в чате на сайте"""
        try:
            # Находим пользователя по VK ID
            user = self.find_user_by_vk_id(from_id)
            if not user:
                logger.info(f"User with VK ID {from_id} not found")
                return False
            
            # Ищем чат где пользователь участник
            if chat_id:
                chat = Chats.objects.filter(id_chat=chat_id).first()
            else:
                # Ищем активный чат пользователя
                chat = Chats.objects.filter(
                    buyer=user, 
                    is_active=True
                ).order_by('-last_message_at').first()
            
            if not chat:
                logger.info(f"No active chat found for user {user.login}")
                # Создаем новый чат (нужна дополнительная логика)
                return False
            
            # Создаем сообщение
            message = Messages.objects.create(
                chat=chat,
                sender=user,
                message_text=text[:500],  # Ограничиваем длину
                sent_at=datetime.now()
            )
            
            # Обновляем время последнего сообщения в чате
            chat.last_message_at = datetime.now()
            chat.save()
            
            logger.info(f"✅ Message created in chat {chat.id_chat} from user {user.login}")
            return True
            
        except Exception as e:
            logger.error(f"Create message error: {e}")
            return False
    
    def handle_message(self, message):
        """Обработка входящего сообщения из ВК"""
        try:
            peer_id = message.get('peer_id')
            from_id = message.get('from_id')
            text = message.get('text', '')
            
            logger.info(f"📨 VK Message from {from_id}: {text[:50]}")
            
            # Игнорируем сообщения от бота
            if from_id < 0:
                return
            
            # 1. Отправляем подтверждение в ВК
            self.send_vk_message(peer_id, f"✅ Сообщение доставлено в чат сайта!\n\nТекст: {text[:100]}")
            
            # 2. СОЗДАЕМ СООБЩЕНИЕ В ЧАТЕ САЙТА!
            success = self.create_message_in_chat(from_id, text)
            
            if success:
                logger.info(f"✅ Message forwarded to site chat")
                self.send_vk_message(peer_id, f"📬 Сообщение отправлено продавцу. Ожидайте ответа!")
            else:
                logger.warning(f"⚠️ Could not forward message to site chat")
                self.send_vk_message(peer_id, f"⚠️ Не удалось доставить сообщение. Убедитесь, что вы зарегистрированы на сайте с логином {from_id}")
            
        except Exception as e:
            logger.error(f"Handle message error: {e}")
    
    def listen(self):
        if not self.get_long_poll_server():
            logger.error("Failed to get Long Poll server")
            return
        
        logger.info("✅ VK Bot listening for messages...")
        
        while self.running:
            try:
                url = f"{self.server}?act=a_check&key={self.key}&ts={self.ts}&wait=25"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'failed' in data:
                    if data['failed'] == 1:
                        self.ts = data['ts']
                    elif data['failed'] in [2, 3]:
                        self.get_long_poll_server()
                    continue
                
                self.ts = data['ts']
                
                for update in data.get('updates', []):
                    update_type = update.get('type')
                    
                    if update_type == 'message_new':
                        message = update.get('object', {}).get('message', {})
                        if message:
                            self.handle_message(message)
                    
            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                logger.error(f"Long Poll error: {e}")
                time.sleep(5)
    
    def stop(self):
        self.running = False

def run_vk_bot():
    token = settings.VK_GROUP_TOKEN
    group_id = settings.VK_GROUP_ID
    
    if not token or not group_id:
        logger.error("VK_GROUP_TOKEN or VK_GROUP_ID not set")
        print("❌ VK_GROUP_TOKEN или VK_GROUP_ID не заданы!")
        return
    
    bot = VKBot(token, group_id)
    
    try:
        print("🚀 Запуск VK бота...")
        bot.listen()
    except KeyboardInterrupt:
        print("👋 Остановка VK бота...")
        bot.stop()
    except Exception as e:
        logger.error(f"💥 VK Bot error: {e}")
        print(f"❌ Ошибка: {e}")