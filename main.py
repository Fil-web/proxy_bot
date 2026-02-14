import os
import json
import secrets
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# Загружаем переменные из .env файла
load_dotenv()

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
PROXY_SERVER = os.getenv('PROXY_SERVER')
PROXY_PORT = int(os.getenv('PROXY_PORT', 443))
SECRETS_FILE = os.getenv('SECRETS_FILE', '/root/proxy_bot/allowed_users.json')

# Проверка наличия токена
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_allowed_secrets():
    """Загружает список разрешенных секретов из файла."""
    try:
        with open(SECRETS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_allowed_secrets(secrets_dict):
    """Сохраняет словарь секретов в файл."""
    # Создаем директорию, если её нет
    os.makedirs(os.path.dirname(SECRETS_FILE), exist_ok=True)
    with open(SECRETS_FILE, 'w') as f:
        json.dump(secrets_dict, f, indent=4)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    
    # Загружаем текущие ключи
    allowed_users = load_allowed_secrets()
    
    # Проверяем, есть ли у пользователя уже ключ
    if user_id in allowed_users:
        existing_secret = allowed_users[user_id]
        await message.answer(
            f"🔑 Ваш действующий ключ: `{existing_secret}`\n"
            f"🔗 Ссылка для подключения:\n"
            f"`tg://proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={existing_secret}`\n\n"
            f"Если ссылка не работает, скопируйте её и вставьте в настройках Telegram вручную.",
            parse_mode="Markdown"
        )
        return
    
    # Если ключа нет, проверяем подписку на канал
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, int(user_id))
        if chat_member.status in ['member', 'administrator', 'creator']:
            # Генерируем новый уникальный ключ
            new_secret = secrets.token_hex(16)
            
            # Сохраняем в общий файл
            allowed_users[user_id] = new_secret
            save_allowed_secrets(allowed_users)
            
            await message.answer(
                f"✅ Подписка подтверждена!\n\n"
                f"🔑 Ваш личный ключ: `{new_secret}`\n"
                f"🔗 Ссылка для подключения:\n"
                f"`tg://proxy?server={PROXY_SERVER}&port={PROXY_PORT}&secret={new_secret}`\n\n"
                f"Вставьте эту ссылку в настройках Telegram (Настройки > Данные и память > Прокси).",
                parse_mode="Markdown"
            )
        else:
            await message.answer(f"❌ Вы не подписаны на канал {CHANNEL_ID}. Подпишитесь и попробуйте снова.")
    except Exception as e:
        await message.answer("Ошибка при проверке подписки. Попробуйте позже.")
        print(f"Error checking subscription: {e}")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда для просмотра статистики (только для админа)"""
    user_id = str(message.from_user.id)
    
    # Проверяем, админ ли это (можно настроить свои ID)
    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
    
    if user_id in admin_ids:
        allowed_users = load_allowed_secrets()
        active_count = len(allowed_users)
        
        await message.answer(
            f"📊 **Статистика прокси**\n\n"
            f"Всего пользователей: {active_count}\n"
            f"Последние 5:\n" + 
            "\n".join([f"• ID: {uid[:8]}... ключ: {secret[:8]}..." 
                      for uid, secret in list(allowed_users.items())[-5:]])
        )
    else:
        await message.answer("Эта команда только для администраторов.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())