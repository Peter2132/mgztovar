import logging
import re
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buytovar.settings')
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.conf import settings

from .models import Users, Messages, Chats, TelegramManager

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# =====================================================
# ================= DB FUNCTIONS ======================
# =====================================================

@sync_to_async
def get_user_by_login(login):
    return Users.objects.get(login=login)


@sync_to_async
def get_manager_by_chat_id(chat_id):
    return TelegramManager.objects.get(
        telegram_chat_id=chat_id,
        is_active=True
    )


@sync_to_async
def create_or_update_manager(user_id, telegram_chat_id, username):
    return TelegramManager.objects.update_or_create(
        manager_id=user_id,
        defaults={
            "telegram_chat_id": telegram_chat_id,
            "telegram_username": username,
            "is_active": True
        }
    )


@sync_to_async
def get_chat_by_id(chat_id):
    return Chats.objects.select_related("buyer", "product").get(
        id_chat=chat_id
    )


@sync_to_async
def create_message(chat_id, sender_id, text):
    return Messages.objects.create(
        chat_id=chat_id,
        sender_id=sender_id,
        message_text=text,
        sent_at=timezone.now()
    )


@sync_to_async
def update_chat_timestamp(chat_id):
    Chats.objects.filter(id_chat=chat_id).update(
        last_message_at=timezone.now()
    )


@sync_to_async
def get_manager_chats(manager_id):
    return list(
        Chats.objects.filter(
            seller_id=manager_id,
            is_active=True
        )
        .select_related("buyer", "product")
        .order_by("-last_message_at")[:10]
    )


@sync_to_async
def get_last_message(chat_id):
    return (
        Messages.objects
        .filter(chat_id=chat_id)
        .order_by("-sent_at")
        .first()
    )


@sync_to_async
def deactivate_manager(chat_id):
    TelegramManager.objects.filter(
        telegram_chat_id=chat_id
    ).update(is_active=False)


# =====================================================
# ================= HANDLERS ==========================
# =====================================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or ""
    first_name = message.from_user.first_name

    try:
        user = await get_user_by_login(username)

        if user.role_id != 3:
            await message.answer("❌ Вы не являетесь менеджером.")
            return

        await create_or_update_manager(
            user_id=user.id_user,
            telegram_chat_id=user_id,
            username=username
        )

        await message.answer(
            f"✅ Здравствуйте, {first_name}!\n"
            f"Вы зарегистрированы как менеджер."
        )

    except Users.DoesNotExist:
        await message.answer(
            "❌ Пользователь не найден.\n"
            "Username Telegram должен совпадать с логином на сайте."
        )
    except Exception as e:
        logger.error(f"Start error: {e}")
        await message.answer("❌ Ошибка регистрации.")


# =====================================================

@dp.message(Command("chats"))
async def list_chats(message: Message):
    telegram_chat_id = str(message.from_user.id)

    try:
        manager = await get_manager_by_chat_id(telegram_chat_id)
        chats = await get_manager_chats(manager.manager_id)

        if not chats:
            await message.answer("У вас нет активных чатов.")
            return

        response = "📋 Ваши активные чаты:\n\n"

        for chat in chats:
            last_msg = await get_last_message(chat.id_chat)

            response += (
                f"🆔 Чат ID: {chat.id_chat}\n"
                f"👤 Покупатель: {chat.buyer.login}\n"
                f"📦 Товар: {chat.product.title if chat.product else 'Общий чат'}\n"
                f"🕒 Последнее сообщение: "
                f"{last_msg.sent_at.strftime('%d.%m %H:%M') if last_msg else 'Нет'}\n"
                f"----------------------\n"
            )

        await message.answer(response)

    except TelegramManager.DoesNotExist:
        await message.answer("❌ Напишите /start для регистрации.")
    except Exception as e:
        logger.error(f"Chats error: {e}")
        await message.answer("❌ Ошибка загрузки чатов.")


# =====================================================

@dp.message()
async def handle_reply(message: Message):
    if not message.reply_to_message:
        return

    original_text = message.reply_to_message.text

    if "Чат ID:" not in original_text:
        return

    match = re.search(r'Чат ID: (\d+)', original_text)
    if not match:
        return

    chat_id = int(match.group(1))
    telegram_chat_id = str(message.from_user.id)

    try:
        manager = await get_manager_by_chat_id(telegram_chat_id)

        # создаём сообщение
        await create_message(
            chat_id=chat_id,
            sender_id=manager.manager_id,
            text=message.text
        )

        await update_chat_timestamp(chat_id)

        await message.answer("✅ Ответ отправлен.")

    except TelegramManager.DoesNotExist:
        await message.answer("❌ Вы не зарегистрированы. Напишите /start")
    except Chats.DoesNotExist:
        await message.answer("❌ Чат не найден.")
    except Exception as e:
        logger.error(f"Reply error: {e}")
        await message.answer("❌ Ошибка отправки.")


# =====================================================

@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    telegram_chat_id = str(message.from_user.id)

    try:
        await deactivate_manager(telegram_chat_id)
        await message.answer(
            "✅ Уведомления отключены.\n"
            "Чтобы включить снова — напишите /start"
        )
    except Exception as e:
        logger.error(f"Stop error: {e}")
        await message.answer("❌ Ошибка.")